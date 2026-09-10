from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import launch


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(launch, "run_manifest", None)), "launch intent is not durably journaled yet")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "batch.json"
        environment = patch.dict(os.environ, {"WORK_GH_STATE_DIR": str(self.root / "registry")})
        environment.start()
        self.addCleanup(environment.stop)
        self.manifest = {
            "version": 1, "kind": "batch", "batch_id": "batch-1",
            "repository": "owner/repo", "repo_path": str(self.root),
            "profile": "work", "parent_id": "parent", "group": "repo",
            "default_branch": "main", "name_prefix": "work", "extra_instructions": "",
            "selected_issues": [42, 43, 99], "dependencies": {"43": 42},
            "launch_intents": [
                {"id": "owner-stack", "issues": [42, 43], "owner": "work#42", "owner_state": str(self.root / "owner-stack.json"), "status": "planned"},
                {"id": "owner-single", "issues": [99], "owner": "work#99", "owner_state": str(self.root / "owner-single.json"), "status": "planned"},
            ],
            "owners": [], "failures": [],
        }
        self.sessions = {}
        self.launches = []
        self.fail = set()
        self.lose_reply = set()
        self.native_parent = "parent"
        self.discovery = {"available": [{"number": number} for number in [42, 43, 99]], "blocked": [], "in_progress": []}
        for name, replacement in [
            ("read_agent_deck_sessions", lambda profile: list(self.sessions.values())),
            ("session_details", lambda profile, sid: self.sessions[sid]),
            ("repository_for_path", lambda path: ("owner/repo", self.root)),
            ("discover_issues", lambda repository, profile, **kwargs: self.discovery),
            ("check_collisions", lambda *args: None),
        ]:
            patched = patch.object(launch, name, replacement)
            patched.start()
            self.addCleanup(patched.stop)
        patched = patch.object(launch.subprocess, "run", self.run_command)
        patched.start()
        self.addCleanup(patched.stop)

    def run_command(self, command, **kwargs):
        self.assertIn("launch", command)
        persisted = json.loads(self.path.read_text())
        name = command[command.index("--title") + 1]
        self.launches.append(name)
        intent = next(item for item in persisted["launch_intents"] if item["owner"] == name)
        self.assertEqual(intent["status"], "launching")
        self.assertEqual(launch.state.reserved_issues("owner/repo"), {42, 43, 99}, "every stack member must be reserved before the first launch")
        self.assertFalse(Path(intent["owner_state"]).exists(), "dispatcher must not own the worker ledger")
        if name in self.fail:
            return subprocess.CompletedProcess(command, 1, "", "worktree-setup.sh requires trust-scripts")
        sid = "deck-" + name
        self.sessions[sid] = {
            "id": sid, "title": name, "path": str(self.root / name),
            "command": command[command.index("--cmd") + 1],
            "wrapper": command[command.index("--wrapper") + 1], "tool": "pi",
            "parent_session_id": self.native_parent, "profile": "work", "group": "repo",
            "worktree_branch": "feature/" + name, "status": "running",
        }
        if name in self.lose_reply:
            raise subprocess.TimeoutExpired(command, 30)
        return subprocess.CompletedProcess(command, 0, json.dumps({"session_id": sid}), "")

    def test_native_empty_parent_represents_an_unparented_owner(self):
        self.manifest["parent_id"] = None
        self.native_parent = ""
        launch.run_manifest(self.manifest, self.path)
        final = launch.state.load(self.path)
        self.assertFalse(final["failures"])
        self.assertTrue(all(owner["parent_id"] is None for owner in final["owners"]))

    def test_runtime_command_change_is_not_hidden_by_pi_tool_label(self):
        launch.run_manifest(self.manifest, self.path)
        self.sessions["deck-work#42"]["command"] = "pi --model foreign"
        launch.run_manifest(launch.state.load(self.path), self.path)
        self.assertIn("metadata", launch.state.load(self.path)["failures"][0]["error"])

    def test_native_show_may_omit_profile_but_registry_must_attest_it(self):
        with patch.object(launch, "session_details", side_effect=lambda profile, sid: {**self.sessions[sid], "profile": ""}):
            launch.run_manifest(self.manifest, self.path)
            final = launch.state.load(self.path)
            self.assertEqual(len(final["owners"]), 2, final["failures"])
            self.assertFalse(final["failures"])
        self.sessions["deck-work#42"]["profile"] = "other"
        with patch.object(launch, "session_details", side_effect=lambda profile, sid: {**self.sessions[sid], "profile": ""}):
            launch.run_manifest(final, self.path)
        self.assertIn("metadata", launch.state.load(self.path)["failures"][0]["error"])

    def test_registry_and_show_must_name_the_same_session(self):
        launch.run_manifest(self.manifest, self.path)
        with patch.object(launch, "session_details", side_effect=lambda profile, sid: {**self.sessions[sid], "id": "foreign"}):
            launch.run_manifest(launch.state.load(self.path), self.path)
        self.assertIn("metadata", launch.state.load(self.path)["failures"][0]["error"])

    def test_partial_launch_is_persisted_and_resume_does_not_relaunch_stack(self):
        self.fail.add("work#99")
        launch.run_manifest(self.manifest, self.path)
        saved = json.loads(self.path.read_text())
        self.assertEqual([owner["session_id"] for owner in saved["owners"]], ["deck-work#42"])
        self.assertEqual(saved["owners"][0]["branch"], "feature/work#42")
        self.assertEqual(saved["owners"][0]["issues"], [42, 43])
        self.assertIn("trust-scripts", saved["failures"][0]["error"])
        self.fail.clear()
        launch.run_manifest(saved, self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches, ["work#42", "work#99", "work#99"])
        self.assertEqual(len(final["owners"]), 2)
        self.assertEqual(final["failures"], [])

    def test_lost_launch_reply_is_adopted_by_identity_not_replayed(self):
        self.lose_reply.add("work#42")
        launch.run_manifest(self.manifest, self.path)
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches, ["work#42", "work#99"])
        self.assertEqual({item["session_id"] for item in final["owners"]}, {"deck-work#42", "deck-work#99"})

    def test_matching_title_with_wrong_parent_is_not_adopted(self):
        self.lose_reply.add("work#42")
        launch.run_manifest(self.manifest, self.path)
        self.sessions["deck-work#42"]["parent_session_id"] = "foreign-parent"
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches.count("work#42"), 1)
        self.assertEqual(len(final["failures"]), 1)
        self.assertNotIn("deck-work#42", [owner["session_id"] for owner in final["owners"]])

    def test_duplicate_matching_owners_stop_without_a_third_launch(self):
        self.lose_reply.add("work#42")
        launch.run_manifest(self.manifest, self.path)
        self.sessions["duplicate"] = {**self.sessions["deck-work#42"], "id": "duplicate"}
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches.count("work#42"), 1)
        self.assertIn("ambiguous", final["failures"][0]["error"].lower())

    def test_resume_rechecks_github_before_launching_unowned_issue(self):
        self.fail.add("work#99")
        launch.run_manifest(self.manifest, self.path)
        self.fail.clear()
        self.discovery["available"] = [{"number": 42}, {"number": 43}]
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches.count("work#99"), 1)
        self.assertIn("not an open issue", final["failures"][0]["error"])

    def test_terminal_deck_status_is_not_a_successful_owner_outcome(self):
        launch.run_manifest(self.manifest, self.path)
        self.sessions["deck-work#42"]["status"] = "error"
        state_path = self.root / "owner-stack.json"
        state_path.write_text('{"repair_batches_used":2,"outcome":{"status":"stopped_blocked"}}')
        before = state_path.read_bytes()
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        self.assertEqual(state_path.read_bytes(), before)
        final = json.loads(self.path.read_text())
        self.assertTrue(all(owner.get("outcome") != "review_ready" for owner in final["owners"]))
        self.assertEqual(self.launches, ["work#42", "work#99"])

    def test_reserved_descendant_blocks_another_profile_and_batch(self):
        launch.run_manifest(self.manifest, self.path)
        other = {**self.manifest, "batch_id": "another-batch", "profile": "other-profile", "selected_issues": [43], "launch_intents": [{"id": "another-owner", "issues": [43], "owner": "work#43", "owner_state": str(self.root / "another.json"), "status": "planned"}], "dependencies": {}, "owners": [], "failures": []}
        with self.assertRaisesRegex(ValueError, "reserved"):
            launch.run_manifest(other, self.root / "other-batch.json")
        self.assertEqual(self.launches, ["work#42", "work#99"])

    def test_changed_chain_is_not_adopted_from_a_matching_owner_token(self):
        launch.run_manifest(self.manifest, self.path)
        saved = json.loads(self.path.read_text())
        saved["selected_issues"] = [42, 44, 99]
        saved["dependencies"] = {"44": 42}
        saved["launch_intents"][0]["issues"] = [42, 44]
        self.path.write_text(json.dumps(saved))
        launch.run_manifest(saved, self.path)
        final = json.loads(self.path.read_text())
        self.assertEqual(self.launches, ["work#42", "work#99"])
        self.assertTrue(final["failures"], "changed chain identity must not be adopted")

    def test_recorded_worktree_identity_is_not_silently_replaced(self):
        launch.run_manifest(self.manifest, self.path)
        self.sessions["deck-work#42"]["path"] = str(self.root / "different-owner-worktree")
        launch.run_manifest(json.loads(self.path.read_text()), self.path)
        final = json.loads(self.path.read_text())
        self.assertTrue(final["failures"], "resume must compare live and recorded worktree identities")
        self.assertEqual(self.launches, ["work#42", "work#99"])

    def test_manifest_cannot_omit_a_selected_member_from_all_owners(self):
        self.manifest["launch_intents"][0]["issues"] = [42]
        with self.assertRaisesRegex(ValueError, "chain|selected|owner"):
            launch.run_manifest(self.manifest, self.path)
        self.assertFalse(self.launches)

    def test_failed_branch_observation_does_not_prove_retry_is_safe(self):
        # Use the real collision helper rather than this fixture's launch double.
        import importlib.util
        spec = importlib.util.spec_from_file_location("collision_launch", Path(launch.__file__))
        collision_launch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collision_launch)
        with patch.object(collision_launch, "read_agent_deck_sessions", return_value=[]), patch.object(collision_launch.subprocess, "run", return_value=subprocess.CompletedProcess([], 128, "", "cannot read refs")):
            with self.assertRaisesRegex(ValueError, "branch|refs|worktree|inspect"):
                collision_launch.check_collisions(self.root, "owner/repo", "work", [42], "work")


if __name__ == "__main__":
    unittest.main()
