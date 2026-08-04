#!/usr/bin/env python3
"""Unit tests for work-gh-issues discovery helpers."""

from __future__ import annotations

import unittest

from discover import (
    BLOCKED_LABEL,
    issue_numbers,
    open_blocker_numbers,
    open_blockers,
    parse_repository,
)
from launch import parse_dependencies, stack_chains, topological_order, worker_prompt


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
        self.assertNotIn("branch named work#42", prompt)

    def test_worker_prompt_assigns_one_native_stack_owner(self) -> None:
        prompt = worker_prompt("owner/repo", [42, 43], "main")
        self.assertIn("sole writer and native GitHub stack integrator", prompt)
        self.assertIn("#42, #43", prompt)
        self.assertIn("gh stack init --base main", prompt)
        self.assertIn("gh stack sync", prompt)
        self.assertIn("Do not create another worktree", prompt)
        self.assertIn("pr-description as the sole body-authoring path", prompt)

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


if __name__ == "__main__":
    unittest.main()
