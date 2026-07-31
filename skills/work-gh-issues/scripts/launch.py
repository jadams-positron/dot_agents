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
from typing import Any

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
        "--depends-on",
        action="append",
        default=[],
        metavar="CHILD:PARENT",
        help=(
            "Stack CHILD on PARENT. Repeat for each immediate dependency; "
            "each child may have one parent."
        ),
    )
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


def parse_dependencies(raw_values: list[str], issues: list[int]) -> dict[int, int]:
    selected = set(issues)
    dependencies: dict[int, int] = {}
    for raw in raw_values:
        match = re.fullmatch(r"#?(\d+):#?(\d+)", raw.strip())
        if match is None:
            raise ValueError(
                f"invalid dependency {raw!r}; expected CHILD:PARENT, for example 22:21"
            )
        child, parent = (int(value) for value in match.groups())
        if child not in selected or parent not in selected:
            raise ValueError(
                f"dependency {raw!r} references an issue outside the launch set"
            )
        if child == parent:
            raise ValueError(f"issue #{child} cannot depend on itself")
        previous = dependencies.get(child)
        if previous is not None and previous != parent:
            raise ValueError(
                f"issue #{child} has multiple immediate parents; linearize the stack"
            )
        dependencies[child] = parent
    return dependencies


def topological_order(issues: list[int], dependencies: dict[int, int]) -> list[int]:
    """Put each parent before its child while preserving input order otherwise."""
    ordered: list[int] = []
    pending = list(issues)
    complete: set[int] = set()
    while pending:
        ready = [
            issue
            for issue in pending
            if issue not in dependencies or dependencies[issue] in complete
        ]
        if not ready:
            cycle = ", ".join(f"#{issue}" for issue in pending)
            raise ValueError(f"dependency cycle among {cycle}")
        for issue in ready:
            pending.remove(issue)
            ordered.append(issue)
            complete.add(issue)
    return ordered


def repository_default_branch(repository: str) -> str:
    result = subprocess.run(
        [
            "gh",
            "repo",
            "view",
            repository,
            "--json",
            "defaultBranchRef",
            "--jq",
            ".defaultBranchRef.name",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch:
        detail = result.stderr.strip() or "default branch was empty"
        raise ValueError(f"could not resolve default branch for {repository}: {detail}")
    return branch


def worker_prompt(
    repository: str,
    issue: int,
    base_branch: str,
    parent_issue: int | None = None,
) -> str:
    if parent_issue is None:
        stack_contract = f"""This is a stack root. Its PR base is the repository default branch `{base_branch}`. Use that exact branch for rebases and `gh pr create --base`."""
    else:
        stack_contract = f"""This issue is immediately dependent on issue #{parent_issue}. Its PR must be stacked on the parent worker's branch `{base_branch}`, not on the default branch.

Before editing, wait until `origin/{base_branch}` exists, fetch it, and rebase the current issue branch onto it. Configure the current branch's `gh-merge-base` to `{base_branch}`. Keep rebasing onto that branch as the parent changes. Create the draft PR with `--base {base_branch}` and mention the parent issue and base branch in the PR body. Never retarget this PR to the default branch while the parent PR is open."""

    return f"""Run the work-issue skill end to end for GitHub issue {repository}#{issue}.

Agent Deck has already created an isolated worktree and branch for this issue. Treat the current worktree and branch names as authoritative; Agent Deck may apply its configured branch prefix. Use them for work-issue's isolation step. Do not create another worktree and do not rename the branch.

{stack_contract}

Before any upstream push or PR creation, perform a thorough multi-angle review of the complete local diff using the agent-pr-review methodology, but do not post a GitHub review. Run fix-all on every validated finding, rerun all relevant tests, and repeat until clean. Then continue the work-issue workflow.

Create the PR as a draft, assign it to @me, apply the appropriate labels from issue #{issue}, include Closes #{issue}, complete the CI and Bugbot workflow, never merge, and never add AI attribution."""


def launch_command(
    repo: Path,
    repository: str,
    group: str,
    model: str,
    issue: int,
    base_branch: str,
    parent_issue: int | None,
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
        worker_prompt(repository, issue, base_branch, parent_issue),
        "--json",
    ]


def read_agent_deck_sessions() -> list[dict[str, Any]]:
    result = subprocess.run(
        ["agent-deck", "list", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("could not read the Agent Deck session registry")
    try:
        sessions = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent Deck returned an invalid session registry") from exc
    if not isinstance(sessions, list):
        raise TypeError("Agent Deck returned an invalid session registry")
    return sessions


def launched_branch(repository: str, issue: int) -> str:
    """Resolve Agent Deck's actual, possibly prefixed branch name."""
    title = f"work#{issue}"
    candidates: list[dict[str, Any]] = []
    for session in read_agent_deck_sessions():
        if session.get("archived", False) or session.get("title") != title:
            continue
        path_value = session.get("path")
        found = repository_for_path(Path(path_value)) if path_value else None
        if found is not None and found[0].lower() == repository.lower():
            candidates.append(session)
    if not candidates:
        raise ValueError(f"could not find the launched Agent Deck session for #{issue}")

    session = max(candidates, key=lambda item: item.get("created_at", ""))
    path = Path(session["path"])
    result = subprocess.run(
        ["git", "-C", str(path), "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if result.returncode != 0 or not branch:
        raise ValueError(f"could not resolve the launched branch for #{issue}")
    return branch


def check_collisions(repo: Path, repository: str, issues: list[int]) -> None:
    collisions: list[str] = []
    active_sessions = read_agent_deck_sessions()

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
    if shutil.which("gh") is None:
        print("error: gh is not installed or not on PATH", file=sys.stderr)
        return 2

    try:
        issues = collect_issues(args.issues)
        repo = validate_repo(args.repo)
        found = repository_for_path(repo)
        if found is None:
            raise ValueError(f"checkout has no GitHub origin: {repo}")
        repository = found[0]
        group = args.group or repo.name
        dependencies = parse_dependencies(args.depends_on, issues)
        issues = topological_order(issues, dependencies)
        default_branch = repository_default_branch(repository)
        check_collisions(repo, repository, issues)
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    failures: list[int] = []
    branches: dict[int, str] = {}
    for issue in issues:
        parent_issue = dependencies.get(issue)
        if parent_issue is not None and parent_issue not in branches:
            print(
                f"Skipping issue #{issue}: parent issue #{parent_issue} did not launch.",
                file=sys.stderr,
            )
            failures.append(issue)
            continue
        base_branch = (
            branches[parent_issue] if parent_issue is not None else default_branch
        )
        command = launch_command(
            repo,
            repository,
            group,
            args.model,
            issue,
            base_branch,
            parent_issue,
        )
        if args.dry_run:
            print(shlex.join(command))
            branches[issue] = f"<actual branch for work#{issue}>"
            continue

        print(f"Launching issue #{issue} as work#{issue}...", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failures.append(issue)
            continue
        try:
            branches[issue] = launched_branch(repository, issue)
            relationship = (
                f"stacked on #{parent_issue} ({base_branch})"
                if parent_issue is not None
                else f"rooted on {base_branch}"
            )
            print(f"Issue #{issue}: {branches[issue]} -> {relationship}")
        except (TypeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
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
