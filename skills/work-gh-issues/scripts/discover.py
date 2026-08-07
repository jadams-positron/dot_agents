#!/usr/bin/env python3
"""Discover recent GitHub repositories and actionable issues."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CHECKOUT_BASE = Path.home() / "code/github"
BLOCKED_LABEL = re.compile(
    r"(^|[\s:/_-])(blocked|on[\s_-]*hold)([\s:/_-]|$)", re.IGNORECASE
)
ISSUE_PATTERNS = (
    re.compile(r"work#(?P<number>\d+)", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])ja-(?P<number>\d+)(?:-|$)", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])issue[-/#](?P<number>\d+)(?:-|$)", re.IGNORECASE),
)
ISSUE_DETAIL_FIELDS = (
    "number,title,body,comments,labels,assignees,state,url,blockedBy,blocking,"
    "updatedAt"
)


def default_agent_deck_profile() -> str:
    return (
        os.environ.get("AGENTDECK_PROFILE")
        or os.environ.get("AGENT_DECK_PROFILE")
        or "default"
    )


def agent_deck_command(profile: str, *args: str) -> list[str]:
    return ["agent-deck", "-p", profile, *args]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def run_json(command: list[str]) -> Any:
    result = run(command)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise ValueError(f"{shlex_join(command)}: {detail}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{shlex_join(command)} returned invalid JSON") from exc


def shlex_join(command: list[str]) -> str:
    import shlex

    return shlex.join(command)


def parse_repository(remote: str) -> str | None:
    remote = remote.strip().removesuffix("/")
    if "github" not in remote.lower():
        return None

    if "://" in remote:
        path = urlparse(remote).path
    elif ":" in remote:
        path = remote.split(":", 1)[1]
    else:
        path = remote

    parts = path.strip("/").removesuffix(".git").split("/")
    if len(parts) < 2:
        return None
    return "/".join(parts[-2:])


def git_common_root(path: Path) -> Path | None:
    if not path.exists():
        return None
    result = run(
        [
            "git",
            "-C",
            str(path),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ]
    )
    if result.returncode != 0:
        return None
    common_dir = Path(result.stdout.strip()).resolve()
    if common_dir.name != ".git":
        return None
    return common_dir.parent


def repository_for_path(path: Path) -> tuple[str, Path] | None:
    root = git_common_root(path)
    if root is None:
        return None
    result = run(["git", "-C", str(path), "remote", "get-url", "origin"])
    if result.returncode != 0:
        return None
    repository = parse_repository(result.stdout)
    if repository is None:
        return None
    return repository, root


def parse_worktree_porcelain(value: str) -> list[dict[str, str]]:
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in value.splitlines() + [""]:
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, field_value = line.partition(" ")
        current[key] = field_value
    return worktrees


def default_branch_worktree(repo_root: Path, repository: str) -> Path | None:
    github_default = run(
        [
            "gh",
            "repo",
            "view",
            repository,
            "--json",
            "defaultBranchRef",
            "--jq",
            ".defaultBranchRef.name",
        ]
    )
    if github_default.returncode == 0 and github_default.stdout.strip():
        default_branch = github_default.stdout.strip()
    else:
        default_ref = run(
            [
                "git",
                "-C",
                str(repo_root),
                "symbolic-ref",
                "--short",
                "refs/remotes/origin/HEAD",
            ]
        )
        if default_ref.returncode != 0:
            return None
        default_branch = default_ref.stdout.strip().removeprefix("origin/")

    result = run(
        ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"]
    )
    if result.returncode != 0:
        return None
    expected_ref = f"refs/heads/{default_branch}"
    for worktree in parse_worktree_porcelain(result.stdout):
        path_value = worktree.get("worktree")
        if worktree.get("branch") != expected_ref or not path_value:
            continue
        path = Path(path_value)
        inside = run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"]
        )
        if inside.returncode == 0 and inside.stdout.strip() == "true":
            return path.resolve()
    return None


def parse_activity(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def activity_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def recent_repositories(limit: int, profile: str = "default") -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}

    sessions = run_json(agent_deck_command(profile, "list", "--json"))
    if not isinstance(sessions, list):
        raise TypeError("Agent Deck returned an invalid session registry")
    for session in sessions:
        path_value = session.get("path")
        if not path_value:
            continue
        found = repository_for_path(Path(path_value))
        if found is None:
            continue
        repository, root = found
        timestamp = parse_activity(session.get("created_at", ""))
        previous = records.get(repository)
        if previous is None or timestamp > previous["timestamp"]:
            records[repository] = {
                "repository": repository,
                "path": str(root),
                "timestamp": timestamp,
                "source": "agent-deck",
            }

    if CHECKOUT_BASE.is_dir():
        for git_dir in CHECKOUT_BASE.glob("*/*/.git"):
            if not git_dir.is_dir():
                continue
            root = git_dir.parent
            found = repository_for_path(root)
            if found is None:
                continue
            repository, canonical_root = found
            activity_file = git_dir / "logs/HEAD"
            try:
                timestamp = activity_file.stat().st_mtime
            except FileNotFoundError:
                timestamp = git_dir.stat().st_mtime
            previous = records.get(repository)
            if previous is None or timestamp > previous["timestamp"]:
                records[repository] = {
                    "repository": repository,
                    "path": str(canonical_root),
                    "timestamp": timestamp,
                    "source": "git-reflog",
                }

    ordered = sorted(records.values(), key=lambda item: item["timestamp"], reverse=True)
    for record in ordered:
        record["last_activity"] = activity_iso(record.pop("timestamp"))
    return ordered[:limit]


def issue_numbers(text: str) -> set[int]:
    numbers: set[int] = set()
    for pattern in ISSUE_PATTERNS:
        numbers.update(int(match.group("number")) for match in pattern.finditer(text))
    return numbers


def find_repository_root(repository: str, profile: str = "default") -> Path | None:
    conventional = CHECKOUT_BASE / repository
    found = repository_for_path(conventional)
    if found is not None and found[0].lower() == repository.lower():
        return found[1]
    for record in recent_repositories(100, profile):
        if record["repository"].lower() == repository.lower():
            found = repository_for_path(Path(record["path"]))
            if found is not None:
                return found[1]
    return None


def find_checkout(repository: str, profile: str = "default") -> Path | None:
    root = find_repository_root(repository, profile)
    return default_branch_worktree(root, repository) if root is not None else None


def resolve_repository(value: str, profile: str = "default") -> dict[str, str | None]:
    candidate = Path(value).expanduser()
    if candidate.exists():
        found = repository_for_path(candidate)
        if found is None:
            raise ValueError(f"path has no GitHub origin: {candidate}")
        repository, root = found
        checkout = default_branch_worktree(root, repository)
        return {
            "repository": repository,
            "local_path": str(checkout) if checkout else None,
        }

    repository = parse_repository(value)
    if repository is None and re.fullmatch(r"[^/\s]+/[^/\s]+", value):
        repository = value
    if repository is None:
        raise ValueError(
            "repository must be a GitHub URL, OWNER/REPO, or checkout path"
        )
    checkout = find_checkout(repository, profile)
    return {
        "repository": repository,
        "local_path": str(checkout) if checkout else None,
    }


def active_session_issues(repository: str, profile: str = "default") -> set[int]:
    numbers: set[int] = set()
    sessions = run_json(agent_deck_command(profile, "list", "--json"))
    for session in sessions:
        if session.get("archived", False):
            continue
        path_value = session.get("path")
        if not path_value:
            continue
        found = repository_for_path(Path(path_value))
        if found is None or found[0].lower() != repository.lower():
            continue
        numbers.update(issue_numbers(session.get("title", "")))
        numbers.update(issue_numbers(path_value))
    return numbers


def worktree_issues(checkout: Path | None) -> set[int]:
    if checkout is None:
        return set()
    result = run(["git", "-C", str(checkout), "worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return set()
    return issue_numbers(result.stdout)


def branch_issues(checkout: Path | None) -> set[int]:
    if checkout is None:
        return set()
    result = run(
        [
            "git",
            "-C",
            str(checkout),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
            "refs/remotes/origin",
        ]
    )
    if result.returncode != 0:
        return set()
    return issue_numbers(result.stdout)


def open_pr_issues(repository: str) -> dict[int, list[str]]:
    prs = run_json(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            "number,url,headRefName,closingIssuesReferences",
        ]
    )
    linked: dict[int, list[str]] = {}
    for pr in prs:
        numbers = issue_numbers(pr.get("headRefName", ""))
        numbers.update(
            issue["number"]
            for issue in pr.get("closingIssuesReferences", [])
            if isinstance(issue.get("number"), int)
        )
        for number in numbers:
            linked.setdefault(number, []).append(pr["url"])
    return linked


def open_blockers(blocked_by: Any) -> list[str]:
    if not isinstance(blocked_by, dict):
        return []
    blockers: list[str] = []
    for node in blocked_by.get("nodes", []):
        if str(node.get("state", "OPEN")).upper() == "OPEN":
            number = node.get("number")
            blockers.append(f"blocked by #{number}" if number else "open dependency")
    if not blockers and blocked_by.get("totalCount", 0) > len(
        blocked_by.get("nodes", [])
    ):
        blockers.append("blocked by an unresolved dependency")
    return blockers


def open_blocker_numbers(blocked_by: Any) -> list[int]:
    """Return the issue numbers for every visible open dependency."""
    if not isinstance(blocked_by, dict):
        return []
    return sorted(
        node["number"]
        for node in blocked_by.get("nodes", [])
        if isinstance(node.get("number"), int)
        and str(node.get("state", "OPEN")).upper() == "OPEN"
    )


def discover_issues(repository: str, profile: str = "default") -> dict[str, Any]:
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise ValueError("repository must be OWNER/REPO")

    root = find_repository_root(repository, profile)
    checkout = default_branch_worktree(root, repository) if root is not None else None
    session_numbers = active_session_issues(repository, profile)
    worktree_numbers = worktree_issues(root)
    branch_numbers = branch_issues(root)
    pr_numbers = open_pr_issues(repository)
    issues = run_json(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            "number,title,url,labels,assignees,blockedBy,updatedAt",
        ]
    )

    result: dict[str, Any] = {
        "repository": repository,
        "local_path": str(checkout) if checkout else None,
        "available": [],
        "in_progress": [],
        "blocked": [],
    }
    for issue in issues:
        number = issue["number"]
        labels = [label["name"] for label in issue.get("labels", [])]
        assignees = [assignee["login"] for assignee in issue.get("assignees", [])]
        blocked_reasons = open_blockers(issue.get("blockedBy"))
        blocked_reasons.extend(
            f"label: {label}" for label in labels if BLOCKED_LABEL.search(label)
        )
        progress_reasons: list[str] = []
        if assignees:
            progress_reasons.append("assigned to " + ", ".join(assignees))
        if number in session_numbers:
            progress_reasons.append("active Agent Deck session")
        if number in worktree_numbers:
            progress_reasons.append("existing worktree")
        if number in branch_numbers:
            progress_reasons.append("existing issue branch")
        if number in pr_numbers:
            progress_reasons.append("open PR: " + ", ".join(pr_numbers[number]))

        record = {
            "number": number,
            "title": issue["title"],
            "url": issue["url"],
            "labels": labels,
            "assignees": assignees,
            "blocked_by": open_blocker_numbers(issue.get("blockedBy")),
            "updated_at": issue["updatedAt"],
        }
        if blocked_reasons:
            record["reasons"] = blocked_reasons + progress_reasons
            result["blocked"].append(record)
        elif progress_reasons:
            record["reasons"] = progress_reasons
            result["in_progress"].append(record)
        else:
            result["available"].append(record)

    for key in ("available", "in_progress", "blocked"):
        result[key].sort(key=lambda item: item["number"])
    result["counts"] = {
        "open": len(issues),
        "available": len(result["available"]),
        "in_progress": len(result["in_progress"]),
        "blocked": len(result["blocked"]),
    }
    return result


def inspect_issues(repository: str, issue_numbers_to_inspect: list[int]) -> dict[str, Any]:
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise ValueError("repository must be OWNER/REPO")

    issues = []
    for number in issue_numbers_to_inspect:
        issue = run_json(
            [
                "gh",
                "issue",
                "view",
                str(number),
                "--repo",
                repository,
                "--json",
                ISSUE_DETAIL_FIELDS,
            ]
        )
        if not isinstance(issue, dict) or issue.get("number") != number:
            raise TypeError(f"GitHub returned invalid details for issue #{number}")
        issues.append(issue)
    return {"repository": repository, "issues": issues}


def parse_positive_issue_numbers(values: list[str]) -> list[int]:
    tokens = [
        token
        for value in values
        for token in re.split(r"[\s,]+", value.strip())
        if token
    ]
    if not tokens:
        raise ValueError("no issue numbers provided")

    numbers: list[int] = []
    invalid: list[str] = []
    seen: set[int] = set()
    for token in tokens:
        normalized = token.removeprefix("#")
        if not normalized.isascii() or not normalized.isdigit():
            invalid.append(token)
            continue
        number = int(normalized)
        if number < 1:
            invalid.append(token)
            continue
        if number not in seen:
            seen.add(number)
            numbers.append(number)
    if invalid:
        raise ValueError(f"invalid issue number(s): {', '.join(invalid)}")
    return numbers


def print_repositories(records: list[dict[str, Any]]) -> None:
    for index, record in enumerate(records, start=1):
        print(
            f"{index}. {record['repository']} — {record['path']} "
            f"({record['last_activity']})"
        )


def print_issue_section(name: str, issues: list[dict[str, Any]]) -> None:
    print(f"{name} ({len(issues)}):")
    if not issues:
        print("  none")
        return
    for issue in issues:
        reasons = issue.get("reasons")
        suffix = f" [{'; '.join(reasons)}]" if reasons else ""
        print(f"  #{issue['number']} {issue['title']}{suffix}")


def add_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        default=default_agent_deck_profile(),
        help="Agent Deck profile (default: current profile or default).",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    repos_parser = subparsers.add_parser(
        "repos", help="List recently used repositories."
    )
    repos_parser.add_argument("--limit", type=int, default=5)
    repos_parser.add_argument("--json", action="store_true")
    add_profile_argument(repos_parser)

    resolve_parser = subparsers.add_parser(
        "resolve", help="Resolve a repository URL, slug, or checkout path."
    )
    resolve_parser.add_argument("repository")
    resolve_parser.add_argument("--json", action="store_true")
    add_profile_argument(resolve_parser)

    issues_parser = subparsers.add_parser(
        "issues", help="List available, in-progress, and blocked open issues."
    )
    issues_parser.add_argument("repository", help="GitHub OWNER/REPO.")
    issues_parser.add_argument("--json", action="store_true")
    add_profile_argument(issues_parser)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Fetch planning details for selected issues."
    )
    inspect_parser.add_argument("repository", help="GitHub OWNER/REPO.")
    inspect_parser.add_argument("issues", nargs="+", help="Issue numbers.")
    inspect_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "repos":
            records = recent_repositories(args.limit, args.profile)
            if args.json:
                print(json.dumps(records, indent=2))
            else:
                print_repositories(records)
        elif args.command == "resolve":
            result = resolve_repository(args.repository, args.profile)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Repository: {result['repository']}")
                print(f"Local checkout: {result['local_path'] or 'not found'}")
        elif args.command == "issues":
            result = discover_issues(args.repository, args.profile)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Repository: {result['repository']}")
                print(f"Local checkout: {result['local_path'] or 'not found'}")
                print_issue_section("Available", result["available"])
                print_issue_section("Already in progress", result["in_progress"])
                print_issue_section("Blocked", result["blocked"])
        else:
            numbers = parse_positive_issue_numbers(args.issues)
            result = inspect_issues(args.repository, numbers)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Repository: {result['repository']}")
                for issue in result["issues"]:
                    blocked_by = open_blocker_numbers(issue.get("blockedBy"))
                    blocking = sorted(
                        node["number"]
                        for node in issue.get("blocking", {}).get("nodes", [])
                        if isinstance(node.get("number"), int)
                        and str(node.get("state", "OPEN")).upper() == "OPEN"
                    )
                    print(
                        f"  #{issue['number']} {issue['title']} "
                        f"[blocked by: {blocked_by or 'none'}; "
                        f"blocking: {blocking or 'none'}]"
                    )
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
