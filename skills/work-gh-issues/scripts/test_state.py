from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

state = __import__("state") if importlib.util.find_spec("state") else None


def finding(identity="sanitizer", **changes):
    return {
        "id": identity,
        "sourceIds": [f"comment:{identity}"],
        "claim": f"{identity} violates the frozen acceptance check",
        "affectedPremises": ["control bytes reach the output"],
        "evidenceRefs": ["test_control_bytes: observed failure"],
        "counterargument": "The estimated file list excludes this shared path; that is not an authority restriction.",
        "validity": "valid",
        "necessity": "introduced_regression",
        "disposition": "required_now",
        "minimalAction": "Correct the existing sanitizer and retain the reproducer.",
        "file": "internal/sanitize/fields.go",
        "line": 30,
        "severity": "high",
        **changes,
    }


class StateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(state, "the durable owner state module is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "owner.json"
        self.owner = state.new_owner(
            "owner-1", "batch-1", "deck-1", [42],
            {"criteria": ["sanitize control bytes"], "repositories": ["owner/repo"]},
        )

    def test_versioned_atomic_state_survives_restart(self):
        with state.locked(self.path):
            state.save(self.path, self.owner)
        loaded = state.load(self.path, "owner")
        self.assertEqual(loaded, self.owner)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        with patch("state.os.replace", side_effect=OSError("injected before replacement")):
            with self.assertRaisesRegex(OSError, "injected"):
                state.save(self.path, {**loaded, "phase": "implement"})
        self.assertEqual(state.load(self.path), loaded)

    def test_corruption_and_incompatible_versions_are_not_migrated(self):
        for payload in ["{", "[]", '{"version": 99}', json.dumps({**self.owner, "repair_batches_used": -1})]:
            self.path.write_text(payload)
            before = self.path.read_bytes()
            with self.assertRaises((ValueError, TypeError)):
                state.load(self.path)
            self.assertEqual(self.path.read_bytes(), before)

    def test_single_writer_and_foreign_owner_are_rejected(self):
        with state.locked(self.path):
            with self.assertRaisesRegex(ValueError, "writer|locked"):
                with state.locked(self.path):
                    self.fail("second writer entered")
        with self.assertRaisesRegex(ValueError, "owner|session"):
            state.apply(self.owner, {"type": "attempt", "failure": "compile"}, "other-owner", "deck-1")
        with self.assertRaisesRegex(ValueError, "owner|session"):
            state.apply(self.owner, {"type": "attempt", "failure": "compile"}, "owner-1", "other-session")

    def apply(self, **event):
        updated = state.apply(self.owner, event, "owner-1", "deck-1")
        self.owner = updated
        return updated

    def test_local_tdd_iterations_do_not_consume_review_batches(self):
        self.apply(type="attempt", failure="compile")
        self.apply(type="attempt", failure="different acceptance failure")
        self.assertEqual(self.owner["repair_batches_used"], 0)
        self.assertEqual(self.owner["unchanged_attempts"], 1)

    def test_three_unchanged_failures_are_a_separate_backstop(self):
        for _ in range(3):
            self.apply(type="attempt", failure="same crash")
        with self.assertRaisesRegex(ValueError, "progress|attempt"):
            self.apply(type="attempt", failure="same crash")
        self.apply(type="attempt", failure="same crash", progress="New reproducer isolates the shared sanitizer")
        self.assertEqual(self.owner["unchanged_attempts"], 0)
        self.assertEqual(self.owner["repair_batches_used"], 0)

    def test_review_v4_nonrepair_dispositions_preserve_empty_minimal_action(self):
        for disposition, validity, necessity in [("no_change", "valid", "optional"), ("no_change", "invalid", "none"), ("follow_up", "valid", "optional"), ("needs_evidence", "uncertain", "uncertain")]:
            with self.subTest(disposition=disposition, validity=validity):
                item = finding(identity=f"{disposition}-{validity}", disposition=disposition, validity=validity, necessity=necessity, minimalAction="")
                self.apply(type="finding", finding=item)
                self.assertEqual(self.owner["findings"][item["id"]]["minimalAction"], "")
        with self.assertRaisesRegex(ValueError, "minimalAction"):
            self.apply(type="finding", finding=finding(minimalAction=""))

    def test_invalid_claim_cannot_be_kept_unresolved_by_uncertain_necessity(self):
        with self.assertRaisesRegex(ValueError, "validity/necessity"):
            self.apply(type="finding", finding=finding(validity="invalid", necessity="uncertain", disposition="needs_evidence"))

    def test_claim_reuse_ignores_reviewers_anchor_lines_and_unrelated_shas(self):
        original = finding(disposition="follow_up", necessity="optional")
        self.apply(type="finding", finding=original)
        repeated = {**original, "sourceIds": ["different-reviewer:123"], "line": 99}
        self.assertFalse(state.needs_adjudication(self.owner, repeated))
        self.apply(type="finding", finding=repeated)
        stored = self.owner["findings"]["sanitizer"]
        self.assertEqual(stored["sourceIds"], ["comment:sanitizer", "different-reviewer:123"])
        self.assertEqual(stored["disposition"], "follow_up")
        self.apply(type="targets", targets={"feature/work#42": {"headSha": "a" * 40}})
        self.assertFalse(state.needs_adjudication(self.owner, repeated))

    def test_new_evidence_locator_alone_is_not_a_new_fact(self):
        original = finding(disposition="no_change", necessity="optional", evidenceRefs=["old-packet.json", "src/file.py:10"])
        self.apply(type="finding", finding=original)
        relocated = {**original, "evidenceRefs": ["fresh-packet.json", "src/file.py:20"], "line": 20}
        self.assertFalse(state.needs_adjudication(self.owner, relocated))
        self.apply(type="finding", finding=relocated)
        self.assertEqual(self.owner["finding_history"], [])
        self.assertEqual(self.owner["findings"]["sanitizer"]["disposition"], "no_change")
        self.assertIn("fresh-packet.json", self.owner["findings"]["sanitizer"]["evidenceRefs"])

    def test_reopening_copied_ledger_records_invalidates_premise_evidence(self):
        self.apply(type="finding", finding=finding())
        self.apply(type="resolve", id="sanitizer", evidence=["previously passed"])
        previous = copy.deepcopy(self.owner["findings"]["sanitizer"])
        self.apply(type="finding", finding={**previous, "evidenceRefs": ["new failing reproducer"]}, evidence_changed=True, reason="The failure returned")
        self.assertNotIn("resolutionEvidence", self.owner["findings"]["sanitizer"])
        self.assertEqual(self.owner["finding_history"][-1]["finding"], previous)
        self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer"])
        self.apply(type="resolve", id="sanitizer", evidence=["new reproducer passes"])
        self.apply(type="finish_repair", id="repair-1")
        self.apply(type="finding", finding=finding("uncertain", validity="uncertain", necessity="uncertain", disposition="needs_evidence"))
        self.apply(type="investigate", id="uncertain", evidence=["old investigation"])
        previous = copy.deepcopy(self.owner["findings"]["uncertain"])
        self.apply(type="finding", finding={**previous, "evidenceRefs": ["changed premise"]}, requirements_changed=True, reason="A required premise changed")
        self.assertNotIn("investigationEvidence", self.owner["findings"]["uncertain"])
        self.assertEqual(self.owner["finding_history"][-1]["finding"], previous)
        self.apply(type="investigate", id="uncertain", evidence=["fresh investigation"])
        with self.assertRaisesRegex(ValueError, "investigat"):
            self.apply(type="investigate", id="uncertain", evidence=["repeat"])

    def test_relocation_updates_current_and_repair_anchors_without_reopening(self):
        self.apply(type="finding", finding=finding(file="old/path.go", line=10))
        moved = finding(file="new/path.go", line=20)
        self.assertFalse(state.needs_adjudication(self.owner, moved))
        self.apply(type="finding", finding=moved)
        self.assertEqual(self.owner["finding_history"], [])
        self.assertEqual(self.owner["repair_batches_used"], 0)
        self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer"])
        for item in [self.owner["findings"]["sanitizer"], self.owner["repairs"]["repair-1"]["findings"]["sanitizer"]]:
            self.assertEqual((item["file"], item["line"]), ("new/path.go", 20))

    def test_new_evidence_or_changed_premise_reopens_without_erasing_history(self):
        original = finding(disposition="no_change", validity="invalid", necessity="none")
        self.apply(type="finding", finding=original)
        new = finding(evidenceRefs=["new reproducer still fails"])
        self.assertTrue(state.needs_adjudication(self.owner, new, evidence_changed=True))
        self.apply(type="finding", finding=new, evidence_changed=True, reason="New reproducer contradicts the earlier premise")
        self.assertEqual(self.owner["findings"]["sanitizer"]["disposition"], "required_now")
        self.assertEqual(len(self.owner["finding_history"]), 1)
        self.assertEqual(self.owner["finding_history"][0]["finding"]["disposition"], "no_change")
        changed = {**new, "affectedPremises": ["callers now bypass the sanitizer"]}
        self.assertTrue(state.needs_adjudication(self.owner, changed))
        self.assertTrue(state.needs_adjudication(self.owner, new, requirements_changed=True))

    def test_settled_disposition_cannot_be_changed_without_reopening_evidence(self):
        self.apply(type="finding", finding=finding(disposition="follow_up", necessity="optional"))
        with self.assertRaisesRegex(ValueError, "reopen|evidence"):
            self.apply(type="finding", finding=finding())

    def test_invalid_or_optional_feedback_cannot_be_required_now(self):
        for invalid in [finding(validity="invalid"), finding(necessity="optional"), finding(evidenceRefs=[])]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self.apply(type="finding", finding=invalid)

    def test_repair_set_is_frozen_counted_once_and_retained_over_restart(self):
        self.apply(type="finding", finding=finding())
        self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer"])
        state.save(self.path, self.owner)
        self.owner = state.load(self.path)
        self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer"])
        self.assertEqual(self.owner["repair_batches_used"], 1)
        self.apply(type="finding", finding=finding("another"))
        with self.assertRaisesRegex(ValueError, "frozen|set"):
            self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer", "another"])
        with self.assertRaisesRegex(ValueError, "active|finish"):
            self.apply(type="begin_repair", id="repair-2", finding_ids=["another"])

    def test_two_total_review_batches_not_two_per_feedback_source(self):
        for index in range(2):
            identity = f"claim-{index}"
            self.apply(type="finding", finding=finding(identity))
            self.apply(type="begin_repair", id=f"repair-{index}", finding_ids=[identity])
            self.apply(type="resolve", id=identity, evidence=["focused proving test now passes"])
            self.apply(type="finish_repair", id=f"repair-{index}")
        self.apply(type="finding", finding=finding("third"))
        with self.assertRaisesRegex(ValueError, "exhausted|budget"):
            self.apply(type="begin_repair", id="external-review", finding_ids=["third"])
        self.assertEqual(self.owner["repair_batches_used"], 2)

    def test_alternative_search_is_once_per_feature_not_per_patch(self):
        self.apply(type="alternative", issue=42, doubt="A second writer would duplicate existing state ownership")
        with self.assertRaisesRegex(ValueError, "alternative"):
            self.apply(type="alternative", issue=42, doubt="Try again after a patch")
        with self.assertRaisesRegex(ValueError, "doubt"):
            self.apply(type="alternative", issue=43, doubt="")

    def test_investigation_is_once_at_an_unchanged_premise(self):
        self.apply(type="finding", finding=finding(validity="uncertain", necessity="uncertain", disposition="needs_evidence"))
        self.apply(type="investigate", id="sanitizer", evidence=["could not reproduce with the current fixture"])
        with self.assertRaisesRegex(ValueError, "investigat"):
            self.apply(type="investigate", id="sanitizer", evidence=["ask another reviewer"])

    def test_lost_push_response_is_reconciled_with_all_remote_shas(self):
        refs = {"feature/work#42": {"before": "a" * 40, "after": "b" * 40}, "feature/work#43": {"before": "c" * 40, "after": "d" * 40}}
        self.apply(type="push_intent", id="initial", cause="initial", refs=refs)
        self.assertEqual(state.reconcile_push(self.owner, {key: value["before"] for key, value in refs.items()}), "retry_with_lease")
        self.assertEqual(state.reconcile_push(self.owner, {key: value["after"] for key, value in refs.items()}), "already_pushed")
        with self.assertRaisesRegex(ValueError, "remote|partial"):
            state.reconcile_push(self.owner, {"feature/work#42": "b" * 40, "feature/work#43": "c" * 40})
        with self.assertRaisesRegex(ValueError, "remote"):
            state.reconcile_push(self.owner, {"feature/work#42": "f" * 40, "feature/work#43": "d" * 40})
        self.apply(type="push_observed", remote_shas={key: value["after"] for key, value in refs.items()})
        self.assertEqual(self.owner["pushes"]["initial"]["status"], "observed")

    def test_history_publication_has_independent_immutable_identity(self):
        first = {"branch": {"before": "a" * 40, "after": "b" * 40}}
        self.apply(type="push_intent", id="publication-1", cause="initial", refs=first)
        first["branch"]["after"] = "f" * 40
        self.assertEqual(self.owner["pushes"]["publication-1"]["refs"]["branch"]["after"], "b" * 40)
        first["branch"]["after"] = "b" * 40
        self.apply(type="push_observed", remote_shas={"branch": "b" * 40})
        event = {"type": "push_intent", "id": "base-sync", "cause": "history", "reason": "Base advanced; the feature patch is unchanged", "refs": {"branch": {"before": "b" * 40, "after": "c" * 40}}}
        self.apply(**event)
        state.save(self.path, self.owner)
        self.owner = state.load(self.path)
        self.apply(**event)
        self.assertEqual(self.owner["repair_batches_used"], 0)
        self.assertEqual(state.reconcile_push(self.owner, {"branch": "b" * 40}), "retry_with_lease")
        for changed in [{"cause": "initial"}, {"reason": "different operation"}, {"refs": first}]:
            with self.assertRaisesRegex(ValueError, "cannot change"):
                self.apply(**(event | changed))
        with self.assertRaisesRegex(ValueError, "pending"):
            self.apply(**(event | {"id": "another-sync"}))
        self.apply(type="push_observed", remote_shas={"branch": "c" * 40})
        self.assertEqual(self.owner["pushes"]["base-sync"]["status"], "observed")
        self.assertEqual(self.owner["repair_batches_used"], 0)

    def test_each_accepted_repair_has_at_most_one_publication_operation(self):
        for index in range(2):
            identity = f"claim-{index}"
            self.apply(type="finding", finding=finding(identity))
            self.apply(type="begin_repair", id=f"repair-{index}", finding_ids=[identity])
            self.apply(type="resolve", id=identity, evidence=["proving test passed"])
            self.apply(type="finish_repair", id=f"repair-{index}")
        refs = {"branch": {"before": "a" * 40, "after": "b" * 40}}
        event = {"type": "push_intent", "id": "publication-1", "cause": "repair", "repair_ids": ["repair-0", "repair-1"], "refs": refs}
        self.apply(**event)
        self.apply(type="push_observed", remote_shas={"branch": "b" * 40})
        self.apply(**event)
        state.save(self.path, self.owner)
        self.owner = state.load(self.path)
        for repair_id in ["repair-0", "repair-1"]:
            with self.assertRaisesRegex(ValueError, "one.*repair|repair.*publication"):
                self.apply(**(event | {"id": "publication-2", "repair_ids": [repair_id]}))
        self.assertEqual(self.owner["repair_batches_used"], 2)
        self.assertEqual(len(self.owner["pushes"]), 1)

    def test_publication_cause_and_associations_fail_closed(self):
        event = {"type": "push_intent", "id": "initial", "cause": "initial", "refs": {"branch": {"before": "a" * 40, "after": "b" * 40}}}
        for changed in [{"cause": None}, {"cause": "unknown"}, {"cause": "history"}, {"cause": "repair"}, {"cause": "repair", "repair_ids": ["missing"]}, {"repair_ids": ["missing"]}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.apply(**(event | changed))
        self.apply(**event)
        corrupted = copy.deepcopy(self.owner)
        corrupted["pushes"]["initial"].pop("cause", None)
        with self.assertRaisesRegex(ValueError, "cause"):
            state.validate(corrupted)

    def test_required_feedback_has_deadline_and_current_head(self):
        self.apply(type="feedback", ref="branch", head_sha="a" * 40, required=["CI", "Bugbot"], deadline=100, results={"CI": {"head_sha": "a" * 40, "status": "passed"}})
        self.assertEqual(state.feedback_status(self.owner, "branch", "a" * 40, now=50), "waiting")
        self.assertEqual(state.feedback_status(self.owner, "branch", "a" * 40, now=101), "blocked")
        self.assertEqual(state.feedback_status(self.owner, "branch", "b" * 40, now=50), "stale")
        self.apply(type="feedback", ref="branch", head_sha="a" * 40, required=["CI", "Bugbot"], deadline=100, results={name: {"head_sha": "a" * 40, "status": "passed"} for name in ["CI", "Bugbot"]})
        self.assertEqual(state.feedback_status(self.owner, "branch", "a" * 40, now=99), "complete")
        for change in [{"deadline": 200}, {"required": ["CI"]}]:
            with self.assertRaisesRegex(ValueError, "deadline|required|unchanged"):
                self.apply(type="feedback", **({"ref": "branch", "head_sha": "a" * 40, "required": ["CI", "Bugbot"], "deadline": 100, "results": {}} | change))

    def test_explicit_canonical_gate_overrides_low_risk_exemption(self):
        self.owner["feature_contract"].update(risk="low", review_required=False, canonical_abstraction_required=True, review_kind="focused")
        targets = {"branch": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        evidence = {"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["check"], "clean": True, "ancestry": True}
        for review in [None, {"complete": True, "refs": ["focused report"], "blocking": False}]:
            self.apply(type="evidence", evidence=evidence | ({"review": review} if review else {}))
            with self.assertRaisesRegex(ValueError, "review|canonical"):
                state.require_ready(self.owner)
        self.apply(type="evidence", evidence=evidence | {"review": {"complete": True, "refs": ["canonical packet"], "verdict": "ALIGNED WITH FINDINGS"}})
        state.require_ready(self.owner)

    def test_optional_findings_do_not_block_current_evidence_readiness(self):
        self.apply(type="finding", finding=finding(disposition="follow_up", necessity="optional"))
        targets = {"feature/work#42": {"headSha": "a" * 40, "baseSha": "b" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test transcript"]}, "checks": ["current-head CI"], "review": {"verdict": "ALIGNED WITH FINDINGS", "refs": ["complete canonical packet"], "complete": True}, "clean": True, "ancestry": True})
        self.apply(type="outcome", outcome="review_ready", reason="Original acceptance checks and current-target evidence pass")
        self.assertEqual(self.owner["outcome"]["status"], "review_ready")
        self.assertEqual(self.owner["evidence"]["review"]["verdict"], "ALIGNED WITH FINDINGS")

    def test_old_target_packets_real_blockers_and_incomplete_evidence_reject_readiness(self):
        targets = {"feature/work#42": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        evidence = {"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["CI"], "review": {"verdict": "ALIGNED", "refs": ["packet"], "complete": True}, "clean": True, "ancestry": True}
        self.apply(type="evidence", evidence=evidence)
        saved = copy.deepcopy(self.owner)
        for changed in [
            {**evidence, "targets": {"feature/work#42": {"headSha": "b" * 40}}},
            {**evidence, "criteria": {}},
            {**evidence, "review": {"verdict": "EVADES", "refs": ["packet"], "complete": True}},
            {**evidence, "review": {"verdict": "ALIGNED", "refs": [], "complete": False}},
        ]:
            self.owner = copy.deepcopy(saved)
            self.apply(type="evidence", evidence=changed)
            with self.assertRaisesRegex(ValueError, "readiness|evidence|target|criteria|review"):
                self.apply(type="outcome", outcome="review_ready", reason="checks passed")
        self.owner = saved
        self.apply(type="finding", finding=finding())
        with self.assertRaisesRegex(ValueError, "finding|blocker"):
            self.apply(type="outcome", outcome="review_ready", reason="budget exhausted")

    def test_blocked_outcome_is_terminal_idempotent_and_not_goal_completion(self):
        self.apply(type="finding", finding=finding(necessity="safety", severity="blocker"))
        self.apply(type="outcome", outcome="stopped_blocked", reason="Repair budget exhausted with a reproduced security defect")
        first = copy.deepcopy(self.owner)
        self.apply(type="outcome", outcome="stopped_blocked", reason="Repair budget exhausted with a reproduced security defect")
        self.assertEqual(self.owner, first)
        self.assertNotEqual(self.owner["phase"], "complete")
        self.assertNotIn("complete", self.owner.get("goal_binding", {}))
        with self.assertRaisesRegex(ValueError, "terminal|blocked"):
            self.apply(type="begin_repair", id="another", finding_ids=["sanitizer"])

    def test_phase_checkpoint_cannot_bypass_terminal_readiness(self):
        self.apply(type="phase", phase="implement")
        self.assertEqual(self.owner["phase"], "implement")
        with self.assertRaisesRegex(ValueError, "phase|terminal"):
            self.apply(type="phase", phase="review_ready")

    def test_target_bindings_require_full_shas(self):
        for targets in [{"branch": {}}, {"branch": {"headSha": "HEAD"}}, {"branch": {"headSha": "a" * 40, "baseSha": "main"}}]:
            with self.assertRaisesRegex(ValueError, "SHA|target"):
                self.apply(type="targets", targets=targets)

    def test_unresolved_optional_suggestion_is_not_critical_by_severity_alone(self):
        self.apply(type="finding", finding=finding(claim="Cache sanitizer results to avoid repeated work", affectedPremises=["unproven optional optimization"], validity="uncertain", necessity="optional", disposition="needs_evidence", severity="high"))
        self.apply(type="investigate", id="sanitizer", evidence=["speculative optimization; no acceptance/safety/regression consequence found"])
        targets = {"feature/work#42": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test transcript"]}, "checks": ["CI"], "review": {"verdict": "ALIGNED WITH FINDINGS", "refs": ["packet"], "complete": True}, "clean": True, "ancestry": True})
        self.apply(type="outcome", outcome="review_ready", reason="Investigated optional speculation is not an unmet criterion")
        self.assertEqual(self.owner["outcome"]["status"], "review_ready")

    def test_low_risk_contract_does_not_require_a_fabricated_review(self):
        self.owner["feature_contract"].update(risk="low", review_required=False)
        targets = {"feature/work#42": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test transcript"]}, "checks": ["required final gate"], "clean": True, "ancestry": True})
        self.apply(type="outcome", outcome="review_ready", reason="Frozen low-risk policy requires no independent review")
        self.assertEqual(self.owner["outcome"]["status"], "review_ready")

    def test_medium_risk_focused_review_does_not_invent_a_native_verdict(self):
        self.owner["feature_contract"].update(risk="medium", review_kind="focused")
        targets = {"branch": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["gate"], "review": {"refs": ["independent correctness report"], "complete": True, "blocking": False}, "clean": True, "ancestry": True})
        self.apply(type="outcome", outcome="review_ready", reason="Required focused review has no blockers")
        self.assertNotIn("verdict", self.owner["evidence"]["review"])

    def test_high_risk_cannot_replace_a_canonical_packet_with_a_boolean(self):
        self.owner["feature_contract"].update(risk="high", review_kind="focused")
        targets = {"branch": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["gate"], "review": {"refs": ["opinion"], "complete": True, "blocking": False}, "clean": True, "ancestry": True})
        with self.assertRaisesRegex(ValueError, "native|canonical|review"):
            self.apply(type="outcome", outcome="review_ready", reason="Caller claims the opinion passes")

    def test_current_feedback_failure_cannot_be_hidden_by_summary_evidence(self):
        targets = {"feature/work#42": {"headSha": "a" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["CI supposedly passed"], "review": {"verdict": "ALIGNED", "refs": ["packet"], "complete": True}, "clean": True, "ancestry": True})
        self.apply(type="feedback", ref="feature/work#42", head_sha="a" * 40, required=["CI"], deadline=100, results={"CI": {"head_sha": "a" * 40, "status": "failed"}})
        with self.assertRaisesRegex(ValueError, "feedback|review|check"):
            self.apply(type="outcome", outcome="review_ready", reason="Ignore failure and trust the summary")

    def test_feedback_readiness_covers_each_latest_stack_ref(self):
        targets = {"base": {"headSha": "a" * 40}, "tip": {"headSha": "b" * 40}}
        self.apply(type="targets", targets=targets)
        self.apply(type="evidence", evidence={"targets": targets, "criteria": {"sanitize control bytes": ["test"]}, "checks": ["CI"], "review": {"verdict": "ALIGNED", "refs": ["packet"], "complete": True}, "clean": True, "ancestry": True})
        self.apply(type="feedback", ref="base", head_sha="a" * 40, required=["CI"], deadline=100, results={"CI": {"head_sha": "a" * 40, "status": "passed"}})
        with self.assertRaisesRegex(ValueError, "feedback|review|check"):
            self.apply(type="outcome", outcome="review_ready", reason="Only one PR checked")
        self.apply(type="feedback", ref="tip", head_sha="c" * 40, required=["CI"], deadline=100, results={"CI": {"head_sha": "c" * 40, "status": "passed"}})
        with self.assertRaisesRegex(ValueError, "feedback|review|check"):
            self.apply(type="outcome", outcome="review_ready", reason="Tip CI belongs to the old SHA")
        self.apply(type="feedback", ref="tip", head_sha="b" * 40, required=["CI"], deadline=100, results={"CI": {"head_sha": "b" * 40, "status": "passed"}})
        self.apply(type="outcome", outcome="review_ready", reason="Every current stack ref checked")

    def test_reopening_same_id_cannot_change_an_active_accepted_set(self):
        self.apply(type="finding", finding=finding())
        self.apply(type="begin_repair", id="repair-1", finding_ids=["sanitizer"])
        with self.assertRaisesRegex(ValueError, "frozen|active|set"):
            self.apply(type="finding", finding=finding(affectedPremises=["a different caller and root cause"]), reason="New review claim changes the accepted premise")

    def test_malformed_outcome_and_unsafe_batch_identity_fail_closed(self):
        for changes in [{"outcome": []}, {"batch_id": "../../other-file"}]:
            with self.assertRaises((ValueError, TypeError)):
                state.validate({**self.owner, **changes})


if __name__ == "__main__":
    unittest.main()
