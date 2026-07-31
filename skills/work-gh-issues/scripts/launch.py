#!/usr/bin/env python3
"""Launch one isolated Agent Deck Codex worker per GitHub issue."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from discover import issue_numbers, repository_for_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch GitHub issues as independent Agent Deck workers."
    )
    parser.add_argument(
        "issues",
        nargs="*",
        help="Issue numbers; accepts spaces, commas, and optional # prefixes.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Local checkout for the selected GitHub repository.",
    )
    parser.add_argument(
        "--group",
        help="Agent Deck group (default: repository directory name).",
    )
    parser.add_argument("--model", default="gpt-5.6-sol", help="Codex model ID.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print launch commands without creating sessions or worktrees.",
    )
    return parser.parse_args()


def collect_issues(raw_values: list[str]) -> list[int]:
    if not raw_values:
        try:
            answer = input(
                "Which GitHub issue numbers should I launch? "
                "Provide a space- or comma-separated list: "
            )
        except EOFError as exc:
            raise ValueError("no issue numbers provided") from exc
        raw_values = [answer]

    tokens = [
        token
        for value in raw_values
        for token in re.split(r"[\s,]+", value.strip())
        if token
    ]
    if not tokens:
        raise ValueError("no issue numbers provided")

    issues: list[int] = []
    invalid: list[str] = []
    seen: set[int] = set()
    for token in tokens:
        normalized = token.removeprefix("#")
        if not normalized.isascii() or not normalized.isdigit():
            invalid.append(token)
            continue
        issue = int(normalized)
        if issue < 1:
            invalid.append(token)
            continue
        if issue not in seen:
            seen.add(issue)
            issues.append(issue)

    if invalid:
        raise ValueError(f"invalid issue number(s): {', '.join(invalid)}")
    return issues


def validate_repo(repo: Path) -> Path:
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"repository does not exist: {repo}")

    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"not a git checkout: {repo}")
    return Path(result.stdout.strip()).resolve()


def worker_prompt(repository: str, issue: int) -> str:
    return f"""Run the work-issue skill end to end for GitHub issue {repository}#{issue}.

Agent Deck has already created an isolated worktree and branch for this issue. Treat the current worktree and branch names as authoritative; Agent Deck may apply its configured branch prefix. Use them for work-issue's isolation step. Do not create another worktree and do not rename the branch.

Before any upstream push or PR creation, perform a thorough multi-angle review of the complete local diff using the agent-pr-review methodology, but do not post a GitHub review. Run fix-all on every validated finding, rerun all relevant tests, and repeat until clean. Then continue the work-issue workflow.

Create the PR as a draft, assign it to @me, apply the appropriate labels from issue #{issue}, include Closes #{issue}, complete the CI and Bugbot workflow, never merge, and never add AI attribution."""


def launch_command(
    repo: Path, repository: str, group: str, model: str, issue: int
) -> list[str]:
    name = f"work#{issue}"
    return [
        "agent-deck",
        "launch",
        str(repo),
        "--title",
        name,
        "--title-lock",
        "--group",
        group,
        "--cmd",
        "codex",
        "--model",
        model,
        "--worktree",
        name,
        "--new-branch",
        "--location",
        "subdirectory",
        "--message",
        worker_prompt(repository, issue),
        "--json",
    ]


def check_collisions(repo: Path, repository: str, issues: list[int]) -> None:
    collisions: list[str] = []
    sessions = subprocess.run(
        ["agent-deck", "list", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if sessions.returncode != 0:
        raise ValueError("could not read the Agent Deck session registry")
    try:
        active_sessions = json.loads(sessions.stdout)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("Agent Deck returned an invalid session registry") from exc
    if not isinstance(active_sessions, list):
        raise TypeError("Agent Deck returned an invalid session registry")

    for issue in issues:
        name = f"work#{issue}"
        for session in active_sessions:
            if session.get("archived", False) or session.get("title") != name:
                continue
            path_value = session.get("path")
            found = repository_for_path(Path(path_value)) if path_value else None
            if found is not None and found[0].lower() == repository.lower():
                collisions.append(f"active session {name}")
                break

        branches = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "for-each-ref",
                "--format=%(refname:short)",
                "refs/heads",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if issue in issue_numbers(branches.stdout):
            collisions.append(f"issue branch for #{issue}")

        worktrees = subprocess.run(
            ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        )
        if issue in issue_numbers(worktrees.stdout):
            collisions.append(f"worktree for #{issue}")

    if collisions:
        raise ValueError("existing launch target(s): " + ", ".join(collisions))


def main() -> int:
    args = parse_args()
    if shutil.which("git") is None:
        print("error: git is not installed or not on PATH", file=sys.stderr)
        return 2
    if shutil.which("agent-deck") is None:
        print("error: agent-deck is not installed or not on PATH", file=sys.stderr)
        return 2

    try:
        issues = collect_issues(args.issues)
        repo = validate_repo(args.repo)
        found = repository_for_path(repo)
        if found is None:
            raise ValueError(f"checkout has no GitHub origin: {repo}")
        repository = found[0]
        group = args.group or repo.name
        check_collisions(repo, repository, issues)
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    failures: list[int] = []
    for issue in issues:
        command = launch_command(repo, repository, group, args.model, issue)
        if args.dry_run:
            print(shlex.join(command))
            continue

        print(f"Launching issue #{issue} as work#{issue}...", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failures.append(issue)

    if failures:
        print(
            "Failed issue launch(es): " + ", ".join(f"#{issue}" for issue in failures),
            file=sys.stderr,
        )
        return 1

    action = "Prepared" if args.dry_run else "Launched"
    print(f"{action} {len(issues)} issue worker(s) in group {group}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
