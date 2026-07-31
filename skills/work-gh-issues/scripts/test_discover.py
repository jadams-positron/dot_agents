#!/usr/bin/env python3
"""Unit tests for work-gh-issues discovery helpers."""

from __future__ import annotations

import unittest

from discover import BLOCKED_LABEL, issue_numbers, open_blockers, parse_repository
from launch import worker_prompt


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

    def test_blocked_label_matches_status_and_on_hold(self) -> None:
        self.assertIsNotNone(BLOCKED_LABEL.search("status: blocked"))
        self.assertIsNotNone(BLOCKED_LABEL.search("on-hold"))
        self.assertIsNone(BLOCKED_LABEL.search("enhancement"))

    def test_worker_prompt_uses_current_branch_as_authoritative(self) -> None:
        prompt = worker_prompt("owner/repo", 42)
        self.assertIn("owner/repo#42", prompt)
        self.assertIn("current worktree and branch names as authoritative", prompt)
        self.assertNotIn("branch named work#42", prompt)


if __name__ == "__main__":
    unittest.main()
