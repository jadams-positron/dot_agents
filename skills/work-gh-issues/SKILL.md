---
name: work-gh-issues
description: Discover and fan out actionable GitHub issues into isolated Agent Deck Codex sessions, grouping interdependent work into native GitHub pull-request stacks and applying shared end-to-end quality gates. Use when the user asks to batch, start, launch, work, or orchestrate GitHub issues through Agent Deck, or invokes /work-gh-issues. Resolve a missing repository by offering the five most recently used repositories, and resolve missing issue numbers by listing open, non-blocked, not-already-claimed issues from the selected repository.
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

## Plan dependencies and stacks

Before launching, inspect every selected issue's title, body, comments,
`blockedBy`, and `blocking` relationships. Also inspect enough of the current
code to identify likely shared files, APIs, schemas, migrations, or generated
artifacts. Build a dependency graph from evidence, not title similarity:

- Add a hard edge when GitHub or the issue text says one issue depends on
  another, or when one issue produces an API/schema/artifact the other needs.
- Add an ordering edge when two issues will predictably conflict in the same
  foundational code and there is a clear implementation order.
- Leave unrelated issues independent. A shared label or subsystem alone is not
  enough to stack them.
- If a selected issue has an open prerequisite outside the selection, do not
  launch it silently. Include the prerequisite or omit the dependent issue and
  tell the human.

A PR can have only one immediate base. Convert each connected component into a
reviewable topological chain. Preserve true prerequisite order; serialize
otherwise-independent siblings only when their expected overlap makes that
worthwhile. Detect cycles and ask the human instead of inventing an order.

GitHub recognizes a chain of ordinary PR base/head branches as a pull-request
stack and exposes it through GraphQL `PullRequest.stack` and `stackEntry`.
Current `gh` does not have a separate stack-creation command: create the root
against the default branch, and create each child against the immediately
preceding issue branch.

## Launch workers

Run the bundled launcher instead of reconstructing commands:

```bash
python3 <skill-dir>/scripts/launch.py \
  --repo <local-path> <issue> [<issue> ...] \
  [--depends-on <child>:<immediate-parent> ...]
```

Example: `--depends-on 22:21 --depends-on 23:22` creates a three-PR stack.
The launcher topologically orders the sessions, resolves Agent Deck's actual
possibly-prefixed parent branch after each launch, and gives that exact base to
the child worker. Independent roots still run independently.

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
3. For a stack child, wait for the parent branch, rebase onto it before editing,
   keep it as the branch's `gh-merge-base`, and create the PR with that exact
   `--base` instead of the default branch.
4. Before the first push or PR creation, perform a thorough local multi-angle
   review using `agent-pr-review` methodology, run `fix-all` on every validated
   finding, and rerun relevant tests until clean.
5. Create a draft PR assigned to `@me`, apply appropriate issue labels, include
   `Closes #<issue>`, complete CI and Bugbot, squash iterative cleanup commits
   during the final `work-issue` history pass, never merge, and never add AI
   attribution.

`agent-pr-review` itself requires a remote PR and posts a pending review, so the
pre-push gate uses its methodology locally rather than its posting step.

## Report

Report each successful launch and failure, each root-to-child stack order and
base branch, plus any normalization Agent Deck applied to branch/worktree
names. Give the scoped-view command:

```bash
agent-deck -g <group>
```
