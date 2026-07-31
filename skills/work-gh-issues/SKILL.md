---
name: work-gh-issues
description: Discover and fan out actionable GitHub issues into independent Agent Deck Codex sessions, each with its own worktree and shared end-to-end quality gates. Use when the user asks to batch, start, launch, work, or orchestrate GitHub issues through Agent Deck, or invokes /work-gh-issues. Resolve a missing repository by offering the five most recently used repositories, and resolve missing issue numbers by listing open, non-blocked, not-already-claimed issues from the selected repository.
---

# Work GitHub Issues

Select a repository and actionable issues, then launch one isolated Agent Deck
worker per issue.

## Select the repository

Accept a GitHub URL, `OWNER/REPO`, or a local checkout path from the user's
request. If none is present:

1. Run:

   ```bash
   python3 <skill-dir>/scripts/discover.py repos --limit 5 --json
   ```

2. Ask which repository to use. Include the five numbered candidates with
   their paths and last-activity times. Accept a number, `OWNER/REPO`, URL, or
   path.
3. Stop and wait for the answer. Do not choose a repository for the human.
   Treat the next reply as a continuation of the same invocation.

Recent repositories come from Agent Deck session history, filled to five from
local Git reflog activity under `~/code/github`.

Resolve the selected URL, slug, or path, then run issue discovery:

```bash
python3 <skill-dir>/scripts/discover.py resolve <selection> --json
python3 <skill-dir>/scripts/discover.py issues OWNER/REPO --json
```

If `local_path` is null, ask for the local checkout path before launching. Do
not clone a repository without explicit permission.

## Select issues

Extract positive issue numbers from the request or continuation. Accept `21`,
`#21`, and whitespace- or comma-separated lists.

If no numbers were supplied, use the issue-discovery result to show:

- `available`: open issues with no open GitHub dependency, blocked/on-hold
  label, assignee, active Agent Deck session, existing issue worktree, or open
  issue branch/PR;
- `in_progress`: open issues excluded as already claimed, with reasons;
- `blocked`: open issues excluded by dependencies or labels, with reasons.

If the user explicitly requested all eligible or available issues, select the
entire `available` list. Otherwise ask which available issue numbers to launch,
accept `all`, and stop for the answer. Treat the next reply as a continuation.
Never silently include `in_progress` or `blocked` issues. If nothing is
available, report that and launch nothing.

## Launch workers

Run the bundled launcher instead of reconstructing commands:

```bash
python3 <skill-dir>/scripts/launch.py \
  --repo <local-path> <issue> [<issue> ...]
```

Defaults:

- Agent Deck group: repository directory name; override with `--group` only
  when the user names another group.
- Session title and requested branch handle: `work#<issue>`.
- Worktrees: the repository's configured Agent Deck worktree location.
- Agent and model: Codex `gpt-5.6-sol`.

Agent Deck may apply its configured prefix to the actual branch and worktree
leaf (for example, `feature/work#21` and `feature-work#21`). Treat the paths
returned by `agent-deck launch` as authoritative. Do not add `--no-parent`:
parent linkage supplies status notifications without coupling execution.

The launcher validates the checkout and collisions before creating anything,
de-duplicates issue numbers, locks titles, and continues past an individual
launch failure.

## Worker contract

Each worker receives instructions to:

1. Run `work-issue` end to end for `OWNER/REPO#<issue>`.
2. Reuse the current Agent Deck-created worktree and branch; never create a
   nested worktree or rename the branch.
3. Before the first push or PR creation, perform a thorough local multi-angle
   review using `agent-pr-review` methodology, run `fix-all` on every validated
   finding, and rerun relevant tests until clean.
4. Create a draft PR assigned to `@me`, apply appropriate issue labels, include
   `Closes #<issue>`, complete CI and Bugbot, never merge, and never add AI
   attribution.

`agent-pr-review` itself requires a remote PR and posts a pending review, so the
pre-push gate uses its methodology locally rather than its posting step.

## Report

Report each successful launch and failure, plus any normalization Agent Deck
applied to branch/worktree names. Give the scoped-view command:

```bash
agent-deck -g <group>
```
