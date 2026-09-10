#!/usr/bin/env python3
"""Launch one isolated Agent Deck Pi owner per issue or PR stack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import state
from discover import (
    agent_deck_command,
    default_agent_deck_profile,
    discover_issues,
    issue_numbers,
    parse_positive_issue_numbers,
    read_agent_deck_sessions,
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
    parser.add_argument("--batch-file", type=Path, help="Durable manifest outside disposable worktrees (default: user state directory)")
    parser.add_argument("--resume", action="store_true", help="Reconcile --batch-file before retrying unlaunched owners")
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
    owner_state: str | None = None,
) -> str:
    issue_refs = ", ".join(f"#{issue}" for issue in issues)
    mode = "standalone work-issue" if len(issues) == 1 else "the work-gh-issues stack-owner contract; run work-issue only in delegated mode for members"
    prompt = f"""Run {mode} as the sole root orchestrator for {repository} issues {issue_refs}, ordered bottom-to-tip, under change-control.

Read work-gh-issues sections 5–12 for the canonical owner lifecycle and state protocol, plus change-control/references/upstream-skills.md. Superpowers is consume-only; the owned caller contract governs execution and feedback, not a modified upstream mode. Deliver the smallest correct diff with the original criteria verified. This invocation authorizes necessary in-feature corrections and useful deduplicated follow-up issues, not new product scope, merge, or deploy. Estimated files and LoC are not permission fences. Use two total review-driven repair batches, not two ordinary test fixes. Do not start another root or repeat reviews until no suggestions remain.

Agent Deck already created this isolated worktree and root branch. Inspect and retain their actual names, including configured prefixes. Do not nest, rename, or transfer them. The exact default base is `{base_branch}`. For stack children preserve the actual root prefix, replacing the final `{name_prefix}#{issues[0]}` with `{name_prefix}#<child>`. Only this owner may rebase/sync the stack.

Owner ledger: {owner_state or '$WORK_GH_OWNER_STATE'}. Owner identity: $WORK_GH_OWNER_ID. Launch manifest: $WORK_GH_BATCH_FILE. Initialize the ledger only if absent; otherwise reconcile and resume without resetting decisions or counters. Never edit the launch manifest. Verify report_workflow_outcome is available before beginning feature work, and use its exact owner/session/goal binding for a terminal blocker. A completion sentinel is not proof of review-ready success.

Use pr-description as the sole PR-body authoring path. Preserve current-target canonical review evidence, latest-SHA descendant checks, explicit remote leases, signed commits when required, issue hygiene, and a trailing Bugbot summary. Never merge or add AI attribution to authored commits/PR bodies."""
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
    issues: list[int],
    base_branch: str,
    name_prefix: str,
    extra_instructions: str,
    owner_id: str | None = None,
    owner_state: str | None = None,
    batch_file: str | None = None,
) -> list[str]:
    name = f"{name_prefix}#{issues[0]}"
    runtime = "pi --no-approve"
    if owner_id:
        runtime = "pi"
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
        runtime,
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
            owner_state,
        ),
        "--json",
    )
    if owner_id:
        # Keep Pi as the native tool; an env-prefixed --cmd would identify it as a shell.
        contract = hashlib.sha256(command[command.index("--message") + 1].encode()).hexdigest()
        # {command} includes Agent Deck's shell preflight, not only the Pi executable.
        wrapper = shlex.join(["export", f"WORK_GH_OWNER_ID={owner_id}", f"WORK_GH_OWNER_STATE={owner_state}", f"WORK_GH_BATCH_FILE={batch_file}", f"WORK_GH_LAUNCH_CONTRACT={contract}"])
        command.extend(["--wrapper", f"{wrapper}; {{command}} --no-approve"])
    if parent is not None:
        command.extend(["--parent", parent])
    return command


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
        if branches.returncode != 0:
            raise ValueError("could not inspect branch refs; absence is not established")
        if issue in issue_numbers(branches.stdout):
            collisions.append(f"issue branch for #{issue}")

        worktrees = subprocess.run(
            ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        )
        if worktrees.returncode != 0:
            raise ValueError("could not inspect worktrees; absence is not established")
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
    ) or None
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


def intent_command(manifest, intent, path):
    return launch_command(
        Path(manifest["repo_path"]), manifest["repository"], manifest["profile"],
        manifest["parent_id"], manifest["group"], intent["issues"],
        manifest["default_branch"], manifest["name_prefix"], manifest["extra_instructions"],
        intent["id"], intent["owner_state"], str(path),
    )


def reconcile_owner(manifest, intent, command):
    profile = manifest["profile"]
    wrapper = command[command.index("--wrapper") + 1]
    matches = []
    for session in read_agent_deck_sessions(profile):
        if session.get("archived", False):
            continue
        details = session_details(profile, session["id"])
        if details.get("wrapper") == wrapper or session["id"] == intent.get("session_id"):
            matches.append((session, details))
    if len(matches) > 1:
        raise ValueError("ambiguous launch identity: multiple matching Agent Deck owners")
    if not matches:
        if intent.get("session_id"):
            raise ValueError("recorded owner is missing or archived; do not create a replacement")
        return None
    session, details = matches[0]
    found = repository_for_path(Path(details.get("path", "")))
    expected_repo = repository_for_path(Path(manifest["repo_path"]))
    if (
        details.get("wrapper") != wrapper
        or details.get("id") != session["id"]
        or details.get("tool") != "pi"
        or details.get("command") != command[command.index("--cmd") + 1]
        or session.get("profile") != profile
        or details.get("profile") not in (None, "", profile)
        or details.get("parent_session_id", details.get("parent_id")) not in ((None, "") if manifest["parent_id"] is None else (manifest["parent_id"],))
        or found is None or expected_repo is None
        or found[0].lower() != manifest["repository"].lower()
        or found[1] != expected_repo[1]
    ):
        raise ValueError("launch owner metadata does not prove repository/profile/parent/runtime identity")
    actual = normalize_launch_result({"session_id": details["id"]}, profile, manifest["parent_id"])
    previous = intent.get("actual")
    if previous and any(actual[key] != previous[key] for key in ("worktree", "branch")):
        raise ValueError("recorded owner worktree/branch identity changed; do not silently adopt it")
    actual.update(issues=intent["issues"], owner=intent["owner"], owner_id=intent["id"], owner_state=intent["owner_state"])
    return actual


def run_manifest(manifest, path):
    state.validate(manifest)
    path = Path(path).expanduser().resolve()
    reservation_lock = state.state_directory() / "locks" / hashlib.sha256(manifest["repository"].lower().encode()).hexdigest()
    with state.locked(reservation_lock), state.locked(path):
        if path.exists():
            persisted = state.load(path, "batch")
            state.require(persisted["batch_id"] == manifest["batch_id"], "batch path already belongs to another launch")
            manifest = persisted
        conflicts = state.reserved_issues(manifest["repository"], except_batch=manifest["batch_id"]) & set(manifest["selected_issues"])
        state.require(not conflicts, f"issues reserved by another batch: {sorted(conflicts)}")
        state.save(path, manifest)
        state.register_batch(path, manifest)
        manifest["owners"], manifest["failures"] = [], []
        repo = Path(manifest["repo_path"])
        for intent in manifest["launch_intents"]:
            command = intent_command(manifest, intent, path)
            try:
                actual = reconcile_owner(manifest, intent, command)
                if actual is None:
                    discovery = discover_issues(manifest["repository"], manifest["profile"], except_batch=manifest["batch_id"])
                    dependencies = {int(child): parent for child, parent in manifest["dependencies"].items()}
                    validate_selected_issues(discovery, intent["issues"], dependencies)
                    check_collisions(repo, manifest["repository"], manifest["profile"], intent["issues"], manifest["name_prefix"])
                    intent["status"] = "launching"
                    state.save(path, manifest)
                    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
                    if result.returncode != 0:
                        raise ValueError(launch_failure_detail(result, repo))
                    payload = parse_json_object(result.stdout, "agent-deck launch")
                    session_id = payload.get("session_id") or payload.get("id")
                    state.require(text_identity(session_id), "agent-deck launch did not return a session ID")
                    intent["session_id"] = session_id
                    state.save(path, manifest)
                    actual = reconcile_owner(manifest, intent, command)
                    state.require(actual is not None, "launch receipt could not be reconciled")
                intent.update(status="launched", session_id=actual["session_id"], actual=actual)
                manifest["owners"].append(actual)
            except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
                intent["status"] = "uncertain"
                manifest["failures"].append({"issues": intent["issues"], "owner": intent["owner"], "owner_id": intent["id"], "error": str(exc)})
            state.save(path, manifest)
        manifest["success"] = not manifest["failures"]
        manifest["batch_file"] = str(path)
        manifest["summary"] = f"Reconciled {len(manifest['owners'])} owner session(s) for {len(manifest['selected_issues'])} issue(s) in group {manifest['group']}. Launch success is not feature success."
        state.save(path, manifest)
        return manifest


def text_identity(value):
    return isinstance(value, str) and bool(value.strip())


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
        if args.resume:
            if args.batch_file is None or args.dry_run:
                raise ValueError("--resume requires --batch-file and cannot be combined with --dry-run")
            manifest = state.load(args.batch_file, "batch")
            repo = validate_repo(args.repo)
            state.require(str(repo) == manifest["repo_path"] and args.profile == manifest["profile"], "resume repository/profile does not match the recorded batch")
            state.require(args.parent is None or args.parent == manifest["parent_id"], "resume parent does not match the recorded batch")
            state.require(not args.issues and not args.depends_on and args.instructions_file is None, "resume the frozen selection and instructions, not a changed launch set")
            validate_default_branch_checkout(repo, manifest["default_branch"])
            manifest = run_manifest(manifest, args.batch_file)
            print(json.dumps(manifest, indent=2) if args.json else manifest["summary"])
            return 0 if manifest["success"] else 1
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
    except (OSError, TypeError, ValueError) as exc:
        return command_error(str(exc), args.json)

    current = current_agent_deck_session(args.profile)
    parent = args.parent or (current.get("id") if current else None)
    batch_id = new_batch_id(repository)
    batch_file = (args.batch_file or state.state_directory() / "manifests" / f"{batch_id}.json").expanduser().resolve()
    if batch_file.is_relative_to(repo):
        return command_error("batch state must live outside disposable repository worktrees", args.json)
    manifest: dict[str, Any] = {
        "version": state.VERSION,
        "kind": "batch",
        "batch_id": batch_id,
        "repository": repository,
        "repo_path": str(repo),
        "profile": args.profile,
        "group": group,
        "default_branch": default_branch,
        "parent_id": parent,
        "dry_run": args.dry_run,
        "selected_issues": issues,
        "dependencies": {str(child): parent for child, parent in dependencies.items()},
        "name_prefix": args.name_prefix,
        "extra_instructions": extra_instructions,
        "launch_intents": [],
        "owners": [],
        "failures": [],
    }
    for chain in chains:
        owner_id = uuid.uuid4().hex
        manifest["launch_intents"].append({
            "id": owner_id, "issues": chain, "owner": f"{args.name_prefix}#{chain[0]}",
            "owner_state": str(batch_file.parent / f"{batch_id}.owners" / f"{owner_id}.json"),
            "status": "planned",
        })
    if args.dry_run:
        for intent in manifest["launch_intents"]:
            command = intent_command(manifest, intent, batch_file)
            manifest["owners"].append({**intent, "command": command})
            if not args.json:
                print(shlex.join(command))
    else:
        try:
            manifest = run_manifest(manifest, batch_file)
        except (OSError, TypeError, ValueError) as exc:
            return command_error(str(exc), args.json)

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
