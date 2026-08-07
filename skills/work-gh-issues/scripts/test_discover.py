#!/usr/bin/env python3
"""Unit tests for work-gh-issues discovery helpers."""

from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from discover import (
    BLOCKED_LABEL,
    agent_deck_command,
    inspect_issues,
    issue_numbers,
    open_blocker_numbers,
    open_blockers,
    parse_worktree_porcelain,
    parse_positive_issue_numbers,
    parse_repository,
)
from launch import (
    command_error,
    dependency_contains,
    launch_command,
    launch_failure_detail,
    normalize_launch_result,
    new_batch_id,
    parse_dependencies,
    stack_chains,
    topological_order,
    validate_default_branch_checkout,
    validate_selected_issues,
    worker_prompt,
)


class DiscoveryTests(unittest.TestCase):
    def test_parse_repository_supports_ssh_alias_and_https(self) -> None:
        self.assertEqual(
            parse_repository("git@github.com-personal:owner/repo.git"),
            "owner/repo",
        )
        self.assertEqual(
            parse_repository("https://github.com/owner/repo.git"),
            "owner/repo",
        )

    def test_issue_numbers_recognizes_agent_deck_and_project_branches(self) -> None:
        text = "feature/work#21\n/path/feature-work#22\nja-23-fix\nissue-24"
        self.assertEqual(issue_numbers(text), {21, 22, 23, 24})

    def test_positive_issue_numbers_are_validated_and_deduplicated(self) -> None:
        self.assertEqual(parse_positive_issue_numbers(["#21, 22", "21"]), [21, 22])
        with self.assertRaisesRegex(ValueError, "invalid issue number"):
            parse_positive_issue_numbers(["#0 nope"])

    def test_agent_deck_commands_are_profile_scoped(self) -> None:
        self.assertEqual(
            agent_deck_command("work", "list", "--json"),
            ["agent-deck", "-p", "work", "list", "--json"],
        )

    @patch("launch.uuid.uuid4")
    def test_batch_ids_are_stable_manifest_keys(self, uuid4) -> None:
        uuid4.return_value.hex = "0123456789abcdef"
        self.assertEqual(
            new_batch_id("Positron-AI/api.positron.ai"),
            "positron-ai-api-positron-ai-0123456789ab",
        )

    def test_worktree_porcelain_preserves_branch_ownership(self) -> None:
        records = parse_worktree_porcelain(
            "worktree /repo\n"
            "bare\n\n"
            "worktree /repo/.worktrees/main\n"
            "HEAD abc123\n"
            "branch refs/heads/main\n\n"
        )
        self.assertEqual(records[0], {"worktree": "/repo", "bare": ""})
        self.assertEqual(records[1]["branch"], "refs/heads/main")

    @patch("discover.run_json")
    def test_inspect_issues_fetches_planning_fields(self, run_json) -> None:
        run_json.return_value = {"number": 42, "title": "Test"}
        result = inspect_issues("owner/repo", [42])
        self.assertEqual(result["issues"][0]["number"], 42)
        command = run_json.call_args.args[0]
        self.assertEqual(command[:4], ["gh", "issue", "view", "42"])
        fields = command[command.index("--json") + 1]
        self.assertIn("body", fields)
        self.assertIn("comments", fields)
        self.assertIn("blockedBy", fields)
        self.assertIn("blocking", fields)

    def test_open_blockers_ignores_closed_dependencies(self) -> None:
        blocked_by = {
            "nodes": [
                {"number": 10, "state": "CLOSED"},
                {"number": 11, "state": "OPEN"},
            ],
            "totalCount": 2,
        }
        self.assertEqual(open_blockers(blocked_by), ["blocked by #11"])
        self.assertEqual(open_blocker_numbers(blocked_by), [11])

    def test_blocked_label_matches_status_and_on_hold(self) -> None:
        self.assertIsNotNone(BLOCKED_LABEL.search("status: blocked"))
        self.assertIsNotNone(BLOCKED_LABEL.search("on-hold"))
        self.assertIsNone(BLOCKED_LABEL.search("enhancement"))

    def test_worker_prompt_uses_current_branch_as_authoritative(self) -> None:
        prompt = worker_prompt("owner/repo", [42], "main")
        self.assertIn("owner/repo#42", prompt)
        self.assertIn("current worktree and branch names as authoritative", prompt)
        self.assertIn("independent issue", prompt)
        self.assertIn("pr-description skill as the sole PR-body authoring path", prompt)
        self.assertIn("preserve any Bugbot summary appended at the end byte-for-byte", prompt)
        self.assertNotIn("branch named work#42", prompt)

    def test_worker_prompt_assigns_one_native_stack_owner(self) -> None:
        prompt = worker_prompt("owner/repo", [42, 43], "main")
        self.assertIn("sole writer and native GitHub stack integrator", prompt)
        self.assertIn("#42, #43", prompt)
        self.assertIn("gh stack init --base main", prompt)
        self.assertIn("gh stack sync", prompt)
        self.assertIn("Do not create another worktree", prompt)
        self.assertIn("pr-description as the sole body-authoring path", prompt)
        self.assertIn("preserve any Bugbot summary appended at the end byte-for-byte", prompt)

    def test_worker_prompt_supports_custom_names_and_instructions(self) -> None:
        prompt = worker_prompt(
            "owner/repo",
            [42, 43],
            "main",
            name_prefix="api",
            extra_instructions="Serialize live deployments with lockf.",
        )
        self.assertIn("replacing the final `api#42` with `api#<child>`", prompt)
        self.assertIn("Additional user-authorized worker contract", prompt)
        self.assertIn("Serialize live deployments with lockf.", prompt)

    def test_launch_command_uses_custom_name_and_worker_contract(self) -> None:
        command = launch_command(
            Path("/repo"),
            "owner/repo",
            "work",
            "parent-id",
            "api",
            "gpt-test",
            [42],
            "main",
            "api",
            "Run the live gate.",
        )
        self.assertEqual(command[command.index("--title") + 1], "api#42")
        self.assertEqual(command[command.index("--worktree") + 1], "api#42")
        self.assertEqual(command[:4], ["agent-deck", "-p", "work", "launch"])
        self.assertEqual(command[command.index("--parent") + 1], "parent-id")
        self.assertIn("--assert-done", command)
        self.assertIn("Run the live gate.", command[command.index("--message") + 1])

    def test_dependencies_are_validated_and_topologically_sorted(self) -> None:
        dependencies = parse_dependencies(["#43:#42", "44:43"], [44, 42, 43, 99])
        self.assertEqual(dependencies, {43: 42, 44: 43})
        self.assertEqual(
            topological_order([44, 42, 43, 99], dependencies),
            [42, 99, 43, 44],
        )

    def test_multiple_stack_parents_require_linearization(self) -> None:
        with self.assertRaisesRegex(ValueError, "multiple immediate parents"):
            parse_dependencies(["43:41", "43:42"], [41, 42, 43])

    def test_stack_chains_group_dependencies_under_one_owner(self) -> None:
        self.assertEqual(
            stack_chains([44, 42, 43, 99], {43: 42, 44: 43}),
            [[42, 43, 44], [99]],
        )

    def test_branching_stack_requires_linearization(self) -> None:
        with self.assertRaisesRegex(ValueError, "multiple immediate children"):
            stack_chains([41, 42, 43], {42: 41, 43: 41})

    def test_dependency_cycle_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            topological_order([41, 42], {41: 42, 42: 41})

    def test_dependency_contains_transitive_ancestor(self) -> None:
        dependencies = {44: 43, 43: 42}
        self.assertTrue(dependency_contains(44, 42, dependencies))
        self.assertFalse(dependency_contains(42, 44, dependencies))

    def test_revalidation_accepts_selected_ordered_blocker(self) -> None:
        discovery = {
            "available": [{"number": 42}],
            "in_progress": [],
            "blocked": [
                {
                    "number": 43,
                    "blocked_by": [42],
                    "reasons": ["blocked by #42"],
                }
            ],
        }
        validate_selected_issues(discovery, [42, 43], {43: 42})

    def test_revalidation_rejects_claimed_and_unselected_blockers(self) -> None:
        discovery = {
            "available": [],
            "in_progress": [
                {"number": 42, "reasons": ["active Agent Deck session"]}
            ],
            "blocked": [
                {
                    "number": 43,
                    "blocked_by": [41],
                    "reasons": ["blocked by #41"],
                }
            ],
        }
        with self.assertRaisesRegex(
            ValueError, "active Agent Deck session.*blocked by unselected #41"
        ):
            validate_selected_issues(discovery, [42, 43], {})

    def test_revalidation_rejects_missing_dependency_order(self) -> None:
        discovery = {
            "available": [{"number": 42}],
            "in_progress": [],
            "blocked": [
                {
                    "number": 43,
                    "blocked_by": [42],
                    "reasons": ["blocked by #42"],
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "missing dependency order after #42"):
            validate_selected_issues(discovery, [42, 43], {})

    def test_revalidation_rejects_claimed_blocked_issue(self) -> None:
        discovery = {
            "available": [{"number": 42}],
            "in_progress": [],
            "blocked": [
                {
                    "number": 43,
                    "blocked_by": [42],
                    "reasons": ["blocked by #42", "assigned to octocat"],
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "assigned to octocat"):
            validate_selected_issues(discovery, [42, 43], {43: 42})

    @patch("launch.session_details")
    def test_launch_result_uses_stable_ids_and_paths(self, details) -> None:
        details.return_value = {
            "id": "child-id",
            "title": "work#42",
            "path": "/repo/.worktrees/work#42",
            "parent_session_id": "parent-id",
            "group": "repo",
            "status": "running",
        }
        result = normalize_launch_result(
            {
                "session_id": "child-id",
                "worktree_branch": "feature/work#42",
            },
            "default",
            "parent-id",
        )
        self.assertEqual(result["session_id"], "child-id")
        self.assertEqual(result["parent_id"], "parent-id")
        self.assertEqual(result["branch"], "feature/work#42")
        self.assertEqual(result["worktree"], "/repo/.worktrees/work#42")

    @patch("launch.session_details")
    def test_launch_result_rejects_wrong_parent(self, details) -> None:
        details.return_value = {
            "path": "/repo/.worktrees/work#42",
            "worktree_branch": "feature/work#42",
            "parent_session_id": "other-parent",
        }
        with self.assertRaisesRegex(ValueError, "expected 'parent-id'"):
            normalize_launch_result(
                {"session_id": "child-id"}, "default", "parent-id"
            )

    def test_worktree_trust_failure_has_explicit_remediation(self) -> None:
        result = CompletedProcess(
            args=["agent-deck"],
            returncode=1,
            stdout="",
            stderr="worktree-setup.sh requires trust-scripts",
        )
        detail = launch_failure_detail(result, Path("/repo"))
        self.assertIn("agent-deck worktree trust-scripts /repo", detail)

    @patch("launch.subprocess.run")
    def test_launcher_requires_default_branch_worktree(self, run) -> None:
        run.side_effect = [
            CompletedProcess([], 0, "true\n", ""),
            CompletedProcess([], 0, "feature/work#42\n", ""),
        ]
        with self.assertRaisesRegex(ValueError, "default branch 'main'"):
            validate_default_branch_checkout(Path("/repo"), "main")

    def test_json_errors_remain_machine_readable(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = command_error("not launchable", True)
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            json.loads(output.getvalue()),
            {"success": False, "error": "not launchable"},
        )


if __name__ == "__main__":
    unittest.main()
