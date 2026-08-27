---
name: work-issue
description: This skill should be used when the user asks to work a GitHub issue end to end — claim it, assign it to @me, move it to In Progress, complete applicable issue hygiene, implement it in a fresh git worktree, run an independent clean-context abstraction review plus the fess/fix-all/wiggum quality gates, open a draft PR, babysit CI to green, mark the PR ready, and resolve Cursor Bugbot findings until clean. Triggered by phrases like "start working #N in a worktree", "work issue #N", "take #N through the gates", or "/work-issue N". Merge is never part of the flow.
---

# Work Issue

## Overview

Drive one GitHub issue from number to review-ready PR: read and restate the
scope, claim the issue with complete start-work hygiene, implement exactly that
scope in an isolated worktree, pass an honesty-audit gate chain (`fess` →
`fix-all` → `wiggum`) plus an independent abstraction-alignment review, ship a
draft PR, iterate CI to green, collapse iterative commits into one clean issue
commit, flip to ready, and drain Bugbot findings without re-growing the
history. The human merges; this skill never does.

The default is standalone mode. When `work-gh-issues` designates the current
session as the sole owner of an ordered native `gh stack`, run this skill once
per issue in local stack-member mode: implement, verify, and leave one signed
commit, then return to the stack owner without pushing or creating a PR. The
owner alone submits, synchronizes, and updates the chain.

## Authorization

Invoking this skill is explicit approval to update the issue and its issue
branch: assign it to `@me`, move its delivery-project item to `In Progress`,
complete unambiguous hygiene, commit, push with an explicit refspec, open a
draft PR, mark it ready, and resolve review threads. It also approves
rebasing and `--force-with-lease` with an explicit issue-branch refspec when
tracking a stack parent and during the final history cleanup below. It is NOT
approval to merge, invent project metadata, force-push a base or protected
branch, delete work, or commit in any other checkout or repo.

## Stack ownership

Before changing history or pushing, determine whether the current PR or branch
has an open descendant (`gh pr list --state open --base <branch>`) or belongs to
a native stack. If it does, require an explicit sole stack owner and the full
bottom-to-tip branch order. A per-issue worker is never that owner merely
because it owns one branch.

Only the stack owner may run `gh stack rebase`, `gh stack submit`, or
`gh stack sync`. Every other stack member stops after its local signed commit
and reports its branch, parent, commit SHA, tree SHA, and verification evidence.
If a remote stack branch moves unexpectedly, do not overwrite it: report the
expected and observed SHAs to the owner.

## Workflow

### 1. Read the issue

```bash
gh issue view <N> \
  --json state,title,body,labels,comments,assignees,milestone,parent,subIssues,blockedBy,blocking,projectItems
```

Restate scope and acceptance criteria in one short summary before touching
code. Stop if the issue is closed or an unresolved native blocker is a strict
prerequisite. If the scope is ambiguous or contradicts the code found later,
stop and ask — do not guess a scope expansion.

### 2. Claim and normalize issue hygiene

Run this idempotent gate after accepting the scope and before creating a
worktree or changing code.

1. Assign the issue to the current GitHub user:
   `gh issue edit <N> --add-assignee @me`.
2. Identify the delivery project from the native parent's membership, the
   issue's existing project items, or an explicit repository convention, in
   that order. When several projects remain plausible, ask before choosing. Add
   an unprojected issue only when this resolves one project unambiguously.
   Resolve its live schema and set `Status` to the exact `In Progress` option;
   do not update mirror or archive projects.
3. Use the `file-issue` skill's existing-issue hygiene workflow when available;
   otherwise apply the same checks directly. Apply the smallest useful set of
   existing labels, removing one only when current scope or policy proves it
   stale. Set priority, size, type, milestone, dates, native parent/sub-issue
   links, and native dependency links only from explicit issue context,
   relationships, or repository/project policy. Never invent metadata or
   hardcode project, field, or option IDs.
4. Verify the result:
   `gh issue view <N> --json state,assignees,labels,milestone,parent,subIssues,blockedBy,blocking,projectItems`.
   Confirm the current GitHub user is assigned, the delivery-project item is
   `In Progress`, relationship directions are correct, and every unfilled
   field is intentional. Include this state in the final handoff.

### 3. Isolate

If an orchestrator already created the current worktree and branch, reuse them
exactly; do not create a nested worktree or rename the branch. Otherwise create
a worktree (EnterWorktree tool, or `git worktree add` from the default branch)
and name the branch using the project's convention. Before the first commit,
check project memory / CLAUDE.md for known worktree gotchas and apply them
proactively (examples in this environment: `golangci-lint cache clean`, strip
ambient `MCC_*`/`HOUSTON_*`/`ATLAS_*` env before hook runs, and pass
`-c core.hooksPath=$PWD/.githooks` when the shared hooksPath is an absolute
path into another checkout).

Resolve the intended PR base before editing. An explicit orchestrator-provided
stack base wins; otherwise use the existing PR's `baseRefName`, the current
branch's `gh-merge-base`, or finally the repository default branch. For a stack
child outside the native stack-owner workflow, wait for the parent branch to
exist on `origin`, fetch it, rebase onto it, and set
`branch.<current>.gh-merge-base` to that exact branch. Never quietly flatten a
child onto the default branch while its parent PR is open. Inside the
stack-owner workflow, reuse its one worktree and let `gh stack add` establish
the child branch and parent; do not create another worktree.

### 4. Implement exactly the scope

Make the change the issue asks for — nothing adjacent. Park unrelated
discoveries for a follow-up issue instead of folding them in; if a judgment
call materially expands or shrinks scope (e.g. a "related" cleanup with a
hidden trade-off), prefer the literal issue scope and surface the call through
the `pr-description` skill. Run the issue's own acceptance checks (greps,
commands it names).
Update the changelog per project convention when the change is user-visible.
In a stack, put only this issue's changelog entry in this issue's commit. Treat
shared changelog structure as stack-owner integration scope and validate it
after every rebase; absence of conflict markers does not prove semantic
correctness.

### 5. Gate chain — all before any push

Run in order; each gate acts on the previous one's findings:

1. Project test suites relevant to the change, plus the pre-commit gate run
   manually once so the commit doesn't discover failures.
2. When the issue, repository, or user explicitly requires live validation,
   exercise the deployed behavior and retain reviewable evidence. Capture and
   inspect a screenshot for UI or visual behavior. For nonvisual API, CLI,
   operator, or deployment behavior, retain a sanitized request/response or
   command/output transcript. Never expose credentials, tokens, customer data,
   private infrastructure details, or unrelated desktop content.
3. `fess` — honesty audit of the work; convert uncertainty into verification
   commands, not assertions.
4. `fix-all` — fix every validated fess finding now, upstream-shaped; reverting
   scope creep counts as a fix.
5. `wiggum` — loop until the Definition of Done holds: commit, then dispatch a
   SEPARATE fess subagent to audit the commit (never self-grade), fold real
   findings back in, and keep a standalone branch rebased on its resolved base.
   A stack member does not independently rebase; the stack owner performs the
   cascading rebase. Bounded attempts (default 3) per failing gate, then
   escalate.
6. `abstraction-review` — after `wiggum` has produced the candidate commit,
   apply its `references/independent-dispatch.md` contract
   (`independent-abstraction-review/v1`) as a mandatory `diff`-profile gate.
   Freeze the target ref, full target-tip, merge-base, candidate-head and tree
   OIDs, exact binary diff and SHA-256. In Codex, `fork_turns: "none"` supplies
   fresh context; another harness must provide an equivalent. Harness-specific
   syntax does not weaken the canonical context, target, capability, freshness,
   evidence, or fail-closed requirements. A broader review satisfies this gate
   only when its abstraction leg returns the complete canonical evidence packet
   for the same target.
7. `fix-all` — fix every validated abstraction-review finding now,
   upstream-shaped. An unverified premise
   that needs an owner's answer blocks the gate rather than becoming an assumed
   exception.
8. After any abstraction repair, rerun affected tests and `wiggum` so the fix is
   folded into the same candidate commit, then dispatch a different fresh
   abstraction reviewer against the new exact head. The gate passes only when
   the exact candidate tree has no unresolved abstraction finding.

If `wiggum` changes content after the last abstraction review, repeat the
affected tests and the fresh-agent abstraction gate before pushing. Record the
complete canonical evidence packet and every finding's disposition in the
handoff evidence.

### 6. Ship the draft PR

In local stack-member mode, stop here and return the signed single-commit
handoff to the stack owner. The remaining steps are performed by the owner for
the whole chain using `gh stack submit --auto` and `gh stack sync`.

Commit with why-focused messages during development (no AI attribution, ever).
Before the first push, invoke `pr-description` as the sole PR-body authoring
path. Give it the issue and acceptance criteria, resolved base and head, complete
diff, observed tests and review results, live evidence when required, and stack
context when applicable. Have it write a body file and validate that file with
`--issue <N>`, plus `--require-example` when the change has a meaningful usage
or configuration surface and `--require-live-evidence` when live validation is
required. Do not handwrite a competing summary. Do not advance a PR to ready
while required live evidence is missing or cannot be published safely.

Push with an explicit refspec: `git push -u origin HEAD:<branch>`. Then:

```bash
gh pr create --draft --base <resolved-base> --title "..." --body-file <body-file> \
  --assignee @me --label <labels matching the issue>
```

Verify `gh pr view --json baseRefName` equals the resolved base; correct it with
`gh pr edit --base` before continuing. Fetch the live body and verify that it
matches the validated body file.

### 7. CI to green

Watch checks (`gh pr checks <n> --watch` or poll on a sensible interval). On
failure: fix on the branch, rerun local gates, push, repeat. Three attempts on
the same failing signature without progress → stop and report rather than
thrash.

### 8. Final history cleanup

Keep the PR draft while cleaning its history. Once draft CI is green, update
against the PR's current base, resolve any conflicts with code-grounded intent,
and rerun affected tests. Then collapse every issue-branch commit above that
base — including `fix`, review, CI, and cleanup checkpoints — into one
why-focused commit:

```bash
branch=$(git branch --show-current)
base=$(gh pr view --json baseRefName --jq .baseRefName)
git fetch origin "$base"
git rebase "origin/$base"
pre_cleanup=$(git rev-parse HEAD)
pre_cleanup_tree=$(git rev-parse "${pre_cleanup}^{tree}")
git reset --soft "origin/$base"
git commit -m "<why-focused issue commit>"
test "$pre_cleanup_tree" = "$(git rev-parse 'HEAD^{tree}')"
```

The tree-OID equality is mandatory: history cleanup must not change content.
Run the complete local gate chain after the rewrite. If it finds anything,
apply the fix and use `git commit --amend --no-edit`; never add another commit.
Require a clean worktree and re-check that the base is an ancestor and the
issue-commit count is exactly one. Recheck for open descendants before pushing;
if any exist, hand the branch to its stack owner instead. Otherwise capture the
remote SHA and push with an exact lease:

```bash
expected=$(git rev-parse "refs/remotes/origin/$branch")
git push --force-with-lease="refs/heads/$branch:$expected" \
  origin "HEAD:refs/heads/$branch"
```

If the branch has no issue commits above the base, stop instead of creating an
empty commit. Never use plain `--force`, and never target the base branch.

Rerun CI on the rewritten SHA. Only that SHA may advance to ready.

### 9. Mark ready

When all checks pass on the latest commit: `gh pr ready <n>`.

### 10. Drain Bugbot

Wait for Cursor Bugbot to review the latest commit. For each finding: triage
(use a bugbot-triage agent when available — verdict real / false-positive /
uncertain with code-grounded reasoning), fix real ones, reply to each review
comment in-thread with what was done (or why it's a false positive) and
resolve the thread — never a top-level summary comment. After the history has
been cleaned, fold every real fix into the single issue commit with
`git commit --amend --no-edit`, rerun local gates, and push with the same
exact expected-SHA lease. Do not append `fix: a`, `fix: b`, or similar commits.
Repeat CI and Bugbot until both are clean on the latest SHA.

Invoke `pr-description` again against the final base and head after CI and
Bugbot. Refresh the live body if the implementation, test evidence, examples,
review path, or risk changed. Before rewriting, fetch the live body; if Bugbot
has appended a summary at the end, preserve that complete block byte-for-byte
in the refreshed body and pass the live snapshot to the validator with
`--existing-body`. Remove other generated summaries and AI attribution, then
verify the resulting GitHub body.

Before handoff, fetch the current PR base and verify it is an ancestor of HEAD.
If it moved, rebase, re-squash/amend, and repeat the local/remote gates. Verify
that `git rev-list --count origin/<base>..HEAD` is exactly `1`. Report the PR
URL, state, stack parent/base when applicable, final SHA, and any open judgment
calls. Do not merge.

For a stack owner, a fix or parent-base movement invalidates every descendant
SHA. Amend the owning issue branch, run `gh stack rebase --upstack`, then
`gh stack sync`; refresh the stack manifest and rerun affected checks
bottom-to-tip. Never repair or force-push only the changed parent branch.

## Escalation

Stop and hand back to the human when: the same gate or CI signature fails 3
times without progress; the issue scope turns out ambiguous or wrong against
the code; a rebase conflict can't be resolved without guessing intent; or any
action would delete work or rewrite anything outside the issue branch. A
scoped rebase/history cleanup and explicit issue-branch `--force-with-lease`
are part of the standalone workflow, not escalation conditions. Unexpected
remote movement, missing stack ownership, or a checked-out stack branch in a
second worktree are also escalation conditions.
