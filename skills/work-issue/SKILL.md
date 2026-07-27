---
name: work-issue
description: This skill should be used when the user asks to work a GitHub issue end to end — implement it in a fresh git worktree, run the fess/fix-all/wiggum quality gates, open a draft PR, babysit CI to green, mark the PR ready, and resolve Cursor Bugbot findings until clean. Triggered by phrases like "start working #N in a worktree", "work issue #N", "take #N through the gates", or "/work-issue N". Merge is never part of the flow.
---

# Work Issue

## Overview

Drive one GitHub issue from number to review-ready PR: read and restate the
scope, implement exactly that scope in an isolated worktree, pass an
honesty-audit gate chain (`fess` → `fix-all` → `wiggum`), ship a draft PR,
iterate CI to green, flip to ready, and drain Bugbot findings on the latest
commit. The human merges; this skill never does.

## Authorization

Invoking this skill is explicit approval to commit, push (explicit refspec
only), open a draft PR, mark it ready, and resolve review threads — on the
issue branch only. It is NOT approval to merge, force-push, push to a
protected branch, or commit in any other checkout or repo.

## Workflow

### 1. Read the issue

`gh issue view <N> --json title,body,labels,comments`. Restate scope and
acceptance criteria in one short summary before touching code. If the scope is
ambiguous or contradicts the code found later, stop and ask — do not guess a
scope expansion.

### 2. Isolate

Create a worktree (EnterWorktree tool, or `git worktree add` from the default
branch). Rename any auto-generated branch to the project's convention
(`ja-<issue>-<slug>`, whole name ≤20 chars). Before the first commit, check
project memory / CLAUDE.md for known worktree gotchas and apply them
proactively (examples in this environment: `golangci-lint cache clean`, strip
ambient `MCC_*`/`HOUSTON_*`/`ATLAS_*` env before hook runs, and pass
`-c core.hooksPath=$PWD/.githooks` when the shared hooksPath is an absolute
path into another checkout).

### 3. Implement exactly the scope

Make the change the issue asks for — nothing adjacent. Park unrelated
discoveries for a follow-up issue instead of folding them in; if a judgment
call materially expands or shrinks scope (e.g. a "related" cleanup with a
hidden trade-off), prefer the literal issue scope and surface the call in the
PR body. Run the issue's own acceptance checks (greps, commands it names).
Update the changelog per project convention when the change is user-visible.

### 4. Gate chain — all before any push

Run in order; each gate acts on the previous one's findings:

1. Project test suites relevant to the change, plus the pre-commit gate run
   manually once so the commit doesn't discover failures.
2. `fess` — honesty audit of the work; convert uncertainty into verification
   commands, not assertions.
3. `fix-all` — fix every fess finding now, upstream-shaped; reverting scope
   creep counts as a fix.
4. `wiggum` — loop until the Definition of Done holds: commit, then dispatch a
   SEPARATE fess subagent to audit the commit (never self-grade), fold real
   findings back in, keep the branch rebased on its base. Bounded attempts
   (default 3) per failing gate, then escalate.

### 5. Ship the draft PR

Commit with a why-focused message (no AI attribution, ever). Push with an
explicit refspec: `git push -u origin <branch>`. Then:

```bash
gh pr create --draft --base <default-branch> --title "..." --body "..." \
  --label <labels matching the issue>
```

Body: terse — what/why in a few lines, `Closes #<N>`, and any judgment calls a
reviewer should veto. No AI attribution footers.

### 6. CI to green

Watch checks (`gh pr checks <n> --watch` or poll on a sensible interval). On
failure: fix on the branch, rerun local gates, push, repeat. Three attempts on
the same failing signature without progress → stop and report rather than
thrash.

### 7. Mark ready

When all checks pass on the latest commit: `gh pr ready <n>`.

### 8. Drain Bugbot

Wait for Cursor Bugbot to review the latest commit. For each finding: triage
(use a bugbot-triage agent when available — verdict real / false-positive /
uncertain with code-grounded reasoning), fix real ones, reply to each review
comment in-thread with what was done (or why it's a false positive) and
resolve the thread — never a top-level summary comment. Push fixes and repeat
until Bugbot is clean on the latest commit. Then hand off: report the PR URL,
state, and any open judgment calls. Do not merge.

## Escalation

Stop and hand back to the human when: the same gate or CI signature fails 3
times without progress; the issue scope turns out ambiguous or wrong against
the code; a rebase conflict can't be resolved without guessing intent; or any
action would be destructive (force-push, history rewrite, deleting work).
