#!/usr/bin/env python3
"""Launch one isolated Agent Deck Codex owner per issue or PR stack."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from discover import (
    agent_deck_command,
    default_agent_deck_profile,
    discover_issues,
    issue_numbers,
    parse_positive_issue_numbers,
    repository_for_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch GitHub issues as independent Agent Deck stack owners."
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
    parser.add_argument(
        "--name-prefix",
        default="work",
        help="Session/worktree/branch name prefix before #ISSUE (default: work).",
    )
    parser.add_argument(
        "--instructions-file",
        type=Path,
        help="Append additional worker instructions from this UTF-8 text file.",
    )
    parser.add_argument("--model", default="gpt-5.6-sol", help="Codex model ID.")
    parser.add_argument(
        "--profile",
        default=default_agent_deck_profile(),
        help="Agent Deck profile (default: current profile or default).",
    )
    parser.add_argument(
        "--parent",
        help="Parent Agent Deck session ID (default: current session when available).",
    )
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one aggregate launch manifest as JSON.",
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

    return parse_positive_issue_numbers(raw_values)


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


def stack_chains(issues: list[int], dependencies: dict[int, int]) -> list[list[int]]:
    """Return bottom-to-tip linear chains in stable root order."""
    ordered = topological_order(issues, dependencies)
    child_by_parent: dict[int, int] = {}
    for child, parent in dependencies.items():
        previous = child_by_parent.get(parent)
        if previous is not None:
            raise ValueError(
                f"issue #{parent} has multiple immediate children "
                f"(#{previous} and #{child}); linearize the stack"
            )
        child_by_parent[parent] = child

    chains: list[list[int]] = []
    for root in ordered:
        if root in dependencies:
            continue
        chain = [root]
        while chain[-1] in child_by_parent:
            chain.append(child_by_parent[chain[-1]])
        chains.append(chain)
    return chains


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


def validate_default_branch_checkout(repo: Path, default_branch: str) -> None:
    inside = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
        check=False,
        capture_output=True,
        text=True,
    )
    branch = subprocess.run(
        ["git", "-C", str(repo), "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    current = branch.stdout.strip()
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise ValueError(f"repository must be a real worktree: {repo}")
    if branch.returncode != 0 or current != default_branch:
        display = current or "detached HEAD"
        raise ValueError(
            f"repository must be checked out on default branch {default_branch!r}; "
            f"found {display!r}"
        )


def worker_prompt(
    repository: str,
    issues: list[int],
    base_branch: str,
    name_prefix: str = "work",
    extra_instructions: str = "",
) -> str:
    issue_refs = ", ".join(f"#{issue}" for issue in issues)
    root_issue = issues[0]
    if len(issues) == 1:
        prompt = f"""Run the work-issue skill end to end for GitHub issue {repository}#{root_issue}.

Agent Deck has already created an isolated worktree and branch for this issue. Treat the current worktree and branch names as authoritative; Agent Deck may apply its configured branch prefix. Use them for work-issue's isolation step. Do not create another worktree and do not rename the branch.

This is an independent issue rooted on `{base_branch}`. Use that exact branch for rebases and `gh pr create --base`.

Before any upstream push or PR creation, perform a thorough multi-angle review of the complete local diff using the agent-pr-review methodology, but do not post a GitHub review. Run fix-all on every validated finding, rerun all relevant tests, and repeat until clean. Then continue the work-issue workflow.

Use the pr-description skill as the sole PR-body authoring path. Create a validated rich body from the exact base-to-head diff and observed evidence, include Example Usage when applicable, and refresh it against the final SHA after CI and Bugbot. Before rewriting a live body, preserve any Bugbot summary appended at the end byte-for-byte and validate against the live snapshot with --existing-body.

Create the PR as a draft, assign it to @me, apply the appropriate labels from issue #{root_issue}, include Closes #{root_issue}, complete the CI and Bugbot workflow, never merge, and never add AI attribution."""
        return append_extra_instructions(prompt, extra_instructions)

    prompt = f"""Act as the sole writer and native GitHub stack integrator for {repository} issues {issue_refs}, ordered bottom-to-tip. No other worker owns any branch in this chain.

Agent Deck has created one isolated worktree and the root branch for issue #{root_issue}. Treat the current worktree and branch as authoritative; Agent Deck may have added a prefix. Do not create another worktree, launch per-issue workers, or let another checkout hold a stack branch.

Read and follow the work-gh-issues stack-owner contract and work-issue stack-member mode. Initialize the current root branch with `gh stack init --base {base_branch} <actual-root-branch>`. Process issues in this exact order: {issue_refs}. For each child, derive its branch by preserving the root branch's prefix and replacing the final `{name_prefix}#{root_issue}` with `{name_prefix}#<child>`, then create it with `gh stack add <child-branch>`.

For each issue, run work-issue locally through its gate chain and leave exactly one signed, why-focused commit. Do not push or create that issue's PR independently. Keep only that issue's user-visible changelog entry in its commit.

After all branches pass their local gates, run the local multi-angle review and fix-all workflow across the complete stack. Use pr-description as the sole body-authoring path to write and validate a separate body file for each future PR from only its immediate base-to-head diff; never reuse a cumulative body. Then run `gh stack rebase` and `gh stack submit --auto`, apply the prepared bodies, and correct every PR's title, assignee, labels, `Closes #<issue>`, and immediate base. Record the ordered branches, PRs, bases, worktree, owner, and expected remote SHAs.

Handle CI and Bugbot bottom-to-tip. Amend fixes into the owning issue commit, run `gh stack rebase --upstack`, and use `gh stack sync` to atomically update the chain. Recheck every affected descendant on its new SHA. Refresh each affected PR through pr-description against its final immediate base and head. Before rewriting a live body, preserve any Bugbot summary appended at the end byte-for-byte and validate against the live snapshot with --existing-body. Never repair or push one parent branch in isolation, never merge, and never add AI attribution."""
    return append_extra_instructions(prompt, extra_instructions)


def append_extra_instructions(prompt: str, extra_instructions: str) -> str:
    extra_instructions = extra_instructions.strip()
    if not extra_instructions:
        return prompt
    return f"{prompt}\n\nAdditional user-authorized worker contract:\n\n{extra_instructions}"


def launch_command(
    repo: Path,
    repository: str,
    profile: str,
    parent: str | None,
    group: str,
    model: str,
    issues: list[int],
    base_branch: str,
    name_prefix: str,
    extra_instructions: str,
) -> list[str]:
    name = f"{name_prefix}#{issues[0]}"
    command = agent_deck_command(
        profile,
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
        "--assert-done",
        "--message",
        worker_prompt(
            repository,
            issues,
            base_branch,
            name_prefix,
            extra_instructions,
        ),
        "--json",
    )
    if parent is not None:
        command.extend(["--parent", parent])
    return command


def read_agent_deck_sessions(profile: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        agent_deck_command(profile, "list", "--json"),
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


def check_collisions(
    repo: Path,
    repository: str,
    profile: str,
    issues: list[int],
    name_prefix: str,
) -> None:
    collisions: list[str] = []
    active_sessions = read_agent_deck_sessions(profile)

    for issue in issues:
        name = f"{name_prefix}#{issue}"
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


def dependency_contains(
    child: int, ancestor: int, dependencies: dict[int, int]
) -> bool:
    current = child
    seen: set[int] = set()
    while current in dependencies and current not in seen:
        seen.add(current)
        current = dependencies[current]
        if current == ancestor:
            return True
    return False


def validate_selected_issues(
    discovery: dict[str, Any],
    issues: list[int],
    dependencies: dict[int, int],
) -> None:
    selected = set(issues)
    records: dict[int, tuple[str, dict[str, Any]]] = {}
    for category in ("available", "in_progress", "blocked"):
        for record in discovery.get(category, []):
            records[record["number"]] = (category, record)

    errors: list[str] = []
    for issue in issues:
        found = records.get(issue)
        if found is None:
            errors.append(f"#{issue} is not an open issue")
            continue
        category, record = found
        if category == "available":
            continue
        if category == "in_progress":
            errors.append(f"#{issue}: {'; '.join(record.get('reasons', []))}")
            continue

        blockers = set(record.get("blocked_by", []))
        other_reasons = [
            reason
            for reason in record.get("reasons", [])
            if not reason.startswith("blocked by #")
        ]
        outside = blockers - selected
        unordered = {
            blocker
            for blocker in blockers & selected
            if not dependency_contains(issue, blocker, dependencies)
        }
        if outside:
            other_reasons.append(
                "blocked by unselected "
                + ", ".join(f"#{number}" for number in sorted(outside))
            )
        if unordered:
            other_reasons.append(
                "missing dependency order after "
                + ", ".join(f"#{number}" for number in sorted(unordered))
            )
        if not blockers:
            other_reasons.append("blocked by an unresolved dependency or label")
        if other_reasons:
            errors.append(f"#{issue}: {'; '.join(dict.fromkeys(other_reasons))}")

    if errors:
        raise ValueError(
            "selected issue(s) are no longer launchable: " + " | ".join(errors)
        )


def current_agent_deck_session(profile: str) -> dict[str, Any] | None:
    result = subprocess.run(
        agent_deck_command(profile, "session", "current", "--json"),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        current = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(current, dict) or not current.get("id"):
        return None
    return current


def parse_json_object(value: str, source: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source} returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise TypeError(f"{source} returned invalid JSON")
    return parsed


def session_details(profile: str, session_id: str) -> dict[str, Any]:
    result = subprocess.run(
        agent_deck_command(profile, "session", "show", session_id, "--json"),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise ValueError(f"could not inspect launched session {session_id}: {detail}")
    return parse_json_object(result.stdout, "agent-deck session show")


def normalize_launch_result(
    payload: dict[str, Any],
    profile: str,
    expected_parent: str | None,
) -> dict[str, Any]:
    session_id = payload.get("session_id") or payload.get("id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("agent-deck launch did not return a session ID")

    details = session_details(profile, session_id)
    worktree = (
        payload.get("worktree_path")
        or details.get("worktree_path")
        or details.get("path")
    )
    branch = payload.get("worktree_branch") or details.get("worktree_branch")
    if worktree and not branch:
        result = subprocess.run(
            ["git", "-C", str(worktree), "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()

    parent_id = (
        payload.get("parent_id")
        or details.get("parent_id")
        or details.get("parent_session_id")
    )
    if expected_parent is not None and parent_id != expected_parent:
        raise ValueError(
            f"launched session {session_id} has parent {parent_id!r}; "
            f"expected {expected_parent!r}"
        )
    if not worktree or not branch:
        raise ValueError(
            f"agent-deck launch did not return a usable worktree for {session_id}"
        )

    return {
        "session_id": session_id,
        "parent_id": parent_id,
        "title": payload.get("title") or details.get("title"),
        "group": payload.get("group") or details.get("group"),
        "status": payload.get("status") or details.get("status"),
        "worktree": str(worktree),
        "branch": str(branch),
    }


def launch_failure_detail(
    result: subprocess.CompletedProcess[str], repo: Path
) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or "agent-deck launch failed"
    lowered = detail.lower()
    if "trust-scripts" in lowered or "worktree-setup.sh" in lowered:
        detail += (
            " Inspect the repository scripts, then explicitly approve their current "
            f"content with: agent-deck worktree trust-scripts {shlex.quote(str(repo))}"
        )
    return detail


def emit_status(message: str, json_mode: bool) -> None:
    print(message, file=sys.stderr if json_mode else sys.stdout, flush=True)


def command_error(message: str, json_mode: bool, exit_code: int = 2) -> int:
    if json_mode:
        print(json.dumps({"success": False, "error": message}, indent=2))
    else:
        print(f"error: {message}", file=sys.stderr)
    return exit_code


def new_batch_id(repository: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", repository.lower()).strip("-")
    return f"{slug}-{uuid.uuid4().hex[:12]}"


def main() -> int:
    args = parse_args()
    if shutil.which("git") is None:
        return command_error("git is not installed or not on PATH", args.json)
    if shutil.which("agent-deck") is None:
        return command_error(
            "agent-deck is not installed or not on PATH", args.json
        )
    if shutil.which("gh") is None:
        return command_error("gh is not installed or not on PATH", args.json)

    try:
        issues = collect_issues(args.issues)
        repo = validate_repo(args.repo)
        found = repository_for_path(repo)
        if found is None:
            raise ValueError(f"checkout has no GitHub origin: {repo}")
        repository = found[0]
        group = args.group or repo.name
        if re.fullmatch(r"[A-Za-z0-9._-]+", args.name_prefix) is None:
            raise ValueError(
                "name prefix must contain only letters, digits, dot, underscore, or dash"
            )
        extra_instructions = ""
        if args.instructions_file is not None:
            try:
                extra_instructions = args.instructions_file.read_text(encoding="utf-8")
            except OSError as exc:
                raise ValueError(
                    f"could not read instructions file {args.instructions_file}: {exc}"
                ) from exc
        dependencies = parse_dependencies(args.depends_on, issues)
        chains = stack_chains(issues, dependencies)
        default_branch = repository_default_branch(repository)
        validate_default_branch_checkout(repo, default_branch)
        discovery = discover_issues(repository, args.profile)
        validate_selected_issues(discovery, issues, dependencies)
        check_collisions(
            repo,
            repository,
            args.profile,
            issues,
            args.name_prefix,
        )
    except (TypeError, ValueError) as exc:
        return command_error(str(exc), args.json)

    current = current_agent_deck_session(args.profile)
    parent = args.parent or (current.get("id") if current else None)
    manifest: dict[str, Any] = {
        "batch_id": new_batch_id(repository),
        "repository": repository,
        "repo_path": str(repo),
        "profile": args.profile,
        "group": group,
        "default_branch": default_branch,
        "parent_id": parent,
        "dry_run": args.dry_run,
        "owners": [],
        "failures": [],
    }

    for chain in chains:
        root_issue = chain[0]
        command = launch_command(
            repo,
            repository,
            args.profile,
            parent,
            group,
            args.model,
            chain,
            default_branch,
            args.name_prefix,
            extra_instructions,
        )
        issue_refs = " -> ".join(f"#{issue}" for issue in chain)
        owner_name = f"{args.name_prefix}#{root_issue}"
        if args.dry_run:
            manifest["owners"].append(
                {
                    "issues": chain,
                    "owner": owner_name,
                    "status": "planned",
                    "command": command,
                }
            )
            if not args.json:
                print(shlex.join(command))
            continue

        emit_status(f"Launching {issue_refs} as {owner_name}...", args.json)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            manifest["failures"].append(
                {
                    "issues": chain,
                    "owner": owner_name,
                    "error": launch_failure_detail(result, repo),
                }
            )
            continue
        payload: dict[str, Any] = {}
        try:
            payload = parse_json_object(result.stdout, "agent-deck launch")
            owner = normalize_launch_result(payload, args.profile, parent)
            owner.update({"issues": chain, "owner": owner_name})
            manifest["owners"].append(owner)
            kind = "stack" if len(chain) > 1 else "issue"
            emit_status(
                f"{kind.title()} {issue_refs}: owner {owner_name} "
                f"({owner['branch']}) -> rooted on {default_branch}",
                args.json,
            )
        except (TypeError, ValueError) as exc:
            failure = {"issues": chain, "owner": owner_name, "error": str(exc)}
            session_id = payload.get("session_id") or payload.get("id")
            if isinstance(session_id, str) and session_id:
                failure.update({"session_id": session_id, "launched": True})
            manifest["failures"].append(failure)

    action = "Prepared" if args.dry_run else "Launched"
    manifest["success"] = not manifest["failures"]
    manifest["summary"] = (
        f"{action} {len(manifest['owners'])} owner session(s) for "
        f"{len(issues)} issue(s) in group {group}."
    )
    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(manifest["summary"])
        for failure in manifest["failures"]:
            refs = ", ".join(f"#{issue}" for issue in failure["issues"])
            print(f"Failed {refs}: {failure['error']}", file=sys.stderr)
    return 0 if manifest["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
