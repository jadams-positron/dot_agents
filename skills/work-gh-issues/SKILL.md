---
name: work-gh-issues
description: Discover and fan out actionable GitHub issues into isolated Agent Deck Pi sessions, assigning one owner to each independent issue or native GitHub pull-request stack and applying shared end-to-end quality gates. Use when the user asks to batch, start, launch, work, or orchestrate GitHub issues through Agent Deck, or invokes /work-gh-issues. Resolve a missing repository by offering the five most recently used repositories, and resolve missing issue numbers by listing open, non-blocked, not-already-claimed issues from the selected repository.
---

# Work GitHub Issues

Select a repository and actionable issues, then launch one isolated Agent Deck
worker per issue.

## Select the repository

Accept a GitHub URL, `OWNER/REPO`, or a local checkout path from the user's
request. If none is present:

1. Run:

   ```bash
   python3 <skill-dir>/scripts/discover.py repos \
     --profile <agent-deck-profile> --limit 5 --json
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
python3 <skill-dir>/scripts/discover.py resolve <selection> \
  --profile <agent-deck-profile> --json
python3 <skill-dir>/scripts/discover.py issues OWNER/REPO \
  --profile <agent-deck-profile> --json
```

`local_path` is returned only for a real worktree on the repository's default
branch; a bare repository or feature-only worktree set is not a safe launch
base. If it is null, ask for a default-branch checkout path before launching.
Do not clone or create one without explicit permission.

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

```bash
python3 <skill-dir>/scripts/discover.py inspect OWNER/REPO \
  <issue> [<issue> ...] --json
```

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
worthwhile. Detect cycles or branching chains and ask the human instead of
inventing an order.

Treat repository-wide files such as `CHANGELOG.md`, lockfiles, generated
artifacts, migration registries, and release metadata as explicit write-set
hotspots. If selected issues must all edit one, place them under one stack owner
or designate that owner to make the shared-file edits. After every rebase, also
validate the file's semantic structure; a merge driver can hide duplicate or
misordered entries without producing conflict markers.

Use native `gh stack` commands. One Agent Deck session and worktree owns each
entire chain; never launch one concurrent writer per stack member. Independent
chains still run in parallel. This ownership rule is required because local
worktrees isolate files, not branch history or remote refs, and `gh stack`
cannot adopt a branch checked out in another worktree.

## Launch workers

Run the bundled launcher instead of reconstructing commands:

```bash
python3 <skill-dir>/scripts/launch.py \
  --repo <local-path> <issue> [<issue> ...] \
  [--profile <agent-deck-profile>] [--parent <session-id>] \
  [--group <group>] [--name-prefix <prefix>] \
  [--instructions-file <path>] \
  [--depends-on <child>:<immediate-parent> ...] [--json]
```

Example: `--depends-on 22:21 --depends-on 23:22` creates a three-PR stack.
The launcher validates and topologically orders each chain, then creates one
session for each chain. The root issue supplies the Agent Deck branch and
worktree name; the stack owner derives child branch names from the actual,
possibly-prefixed root branch. Independent roots and chains run independently.

Defaults:

- Agent Deck group: repository directory name; override with `--group` only
  when the user names another group.
- Session title and requested branch handle: `work#<issue>`; override the
  `work` portion with `--name-prefix` when the user names another scheme.
- Worktrees: the repository's configured Agent Deck worktree location.
- Agent and model: Pi with its configured default model. The launcher uses
  `pi --no-approve` so unattended workers cannot stall on project trust; context
  files and global skills still load, while untrusted project-local resources do
  not.

Use `--instructions-file` to append user-specific authorization, validation,
coordination, or deployment constraints to every worker prompt. Do not place
secret values in that file.

Agent Deck may apply its configured prefix to the actual branch and worktree
leaf (for example, `feature/work#21` and `feature-work#21`). Treat the paths
returned by `agent-deck launch` as authoritative. Do not add `--no-parent`:
parent linkage supplies status notifications without coupling execution.

The launcher scopes every Agent Deck lookup to `--profile`, uses `--parent` or
the current Agent Deck session for durable child events, and requests the Agent
Deck completion sentinel. With `--json`, it returns one manifest containing each
batch's stable ID plus each owner's stable session ID, issue chain, branch,
worktree, group, and parent. Conductors store concurrent manifests by batch ID.

Immediately before creating anything, the launcher revalidates that each issue
is still open and unclaimed. A blocked issue is accepted only when every open
blocker is selected and ordered below it in the supplied dependency chain. The
launcher also validates the checkout and collisions, de-duplicates issue
numbers, locks titles, and continues past an individual launch failure.

Agent Deck 1.11 and newer require explicit approval before a non-interactive
launch runs repository-owned `.agent-deck/worktree-*.sh` scripts. Inspect the
scripts and ask the human to approve their current content with
`agent-deck worktree trust-scripts <repo-path>`; never grant trust implicitly.

## Worker and stack-owner contract

Apply `change-control`. A singleton uses standalone `work-issue` as its sole root; the launcher adds no second review chain. For a multi-issue chain, `work-gh-issues` is the sole root and stack owner. It:

1. Reuses the Agent Deck worktree and actual root branch; it creates no sibling
   worktrees and launches no per-issue writers.
2. Runs `gh stack init --base <default> <actual-root-branch>`, then processes
   issues bottom-to-tip. For each child it uses `gh stack add <child-branch>` and
   runs delegated `work-issue`: implement the bounded unit, run focused checks, leave one signed commit, and return without dispatch, broad review, push, PR, or CI.
3. Runs `gh stack rebase` and the affected local verification gates before
   freezing any review target. It then runs one risk-appropriate aggregate review before submission and repairs only blocking or coupled findings within two total repair rounds. It requires a clean worktree,
   freezes edits, fetches the default
   base, and records the default-base ref, full tip, merge-base, stack-tip and
   tree OIDs, ordered stack OIDs and bounds, plus the exact binary diff and
   SHA-256. The review must include the `agent-pr-review` methodology's
   mandatory `abstraction-review` leg under
   `references/independent-dispatch.md`
   (`independent-abstraction-review/v1`) with the `stack` profile. Give the
   reviewer only raw intent and acceptance criteria for every stack issue,
   repository instructions, and the frozen target. Retain the complete
   canonical evidence packet; any contract failure stops the workflow. This
   aggregate leg is distinct from each member's review because it checks
   interactions introduced only by composition. It then invokes
   `pr-description` as the sole body-authoring path for each PR, using that PR's
   immediate base-to-head diff rather than the cumulative stack. When live
   validation is required, it includes an inspected screenshot for visual
   behavior or a sanitized request/response or command/output transcript for
   nonvisual behavior, then validates with
   `--require-live-evidence`. It writes and validates a separate body file for
   every member, then runs `gh stack submit --auto` without another rebase.
   No amend, rebase, sync, or content-changing command may occur between the
   final aggregate review snapshot and submission. If a material code change is required, consume a repair round and rerun only the affected checks and review concerns before submission.
   After submission it applies those bodies and corrects every PR's title,
   assignee, labels, `Closes #<issue>` metadata, and base; no body is reused
   across stack members.
4. Records a manifest containing ordered issues, branches, PRs, bases, expected
   remote SHAs, worktree, and the sole owner. It verifies GitHub's PR bases match
   the chain and that every expected PR is linked to the native stack.
5. Freezes edits while synchronizing. A parent amendment is followed by
   `gh stack rebase --upstack` and `gh stack sync`, which cascade-rebases and
   atomically pushes the chain with leases. It then refreshes expected SHAs and
   rechecks every descendant's mergeability and checks.
6. Handles CI and Bugbot bottom-to-tip within the same two-round budget. Only blocking or coupled fixes enter an issue commit, followed by stack rebase and sync. A material code amendment reruns affected checks and review concerns; a history-only rebase verifies the target without restarting every review. It
   reruns `pr-description` for every affected PR against its final immediate
   base and head. Before each rewrite it fetches the live body and preserves any
   Bugbot summary appended at the end byte-for-byte, using that snapshot as the
   validator's `--existing-body`; it removes other generated attribution. No PR
   becomes ready until the latest SHA of every affected descendant is green.
7. Never merges and never adds AI attribution.

If a worker discovers that another session or checkout moved a stack branch,
it stops before pushing, records the observed and expected SHAs, and hands the
stack back to its owner. It never repairs a shared stack one branch at a time.

`agent-pr-review` itself requires a remote PR and posts a pending review, so the
pre-push gate uses its methodology locally rather than its posting step. That
methodology includes the independent clean-context `abstraction-review` leg;
the worker must not replace it with a general architecture pass or self-review.

## Report

Report each successful launch and failure, the stable Agent Deck session ID for
every root-to-tip stack owner, its default base, plus any normalization Agent
Deck applied to the root branch/worktree name. Give the scoped-view command:

```bash
agent-deck -g <group>
```
