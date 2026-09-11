---
name: work-issue
description: Use when working one GitHub issue through implementation and a review-ready PR, including issue triage, worktree ownership, verification, CI failures, and review feedback.
---

# Work Issue

Drive one issue to a review-ready PR under `change-control`. The human merges.

## Modes

In **standalone mode**, this is the sole root orchestrator and owns scope, explicit user limits, dispatch, repairs, commits, reviews, pushes, CI, and PR state.

Use **delegated mode** only when an outer workflow names itself as root. Read the issue, implement the authorized unit, run focused checks, create the requested local commit when authorized, and return candidate evidence. Do not dispatch, broadly review, push, open a PR, handle CI, retry orchestration gates, or modify scope. Stack members use delegated mode; the stack owner is root.

## Authorization

Standalone invocation authorizes assigning `@me`, setting an unambiguous delivery project to `In Progress`, issue-branch commits, explicit-refspec pushes, a draft PR, ready state, and resolved review threads. It does not authorize merge, invented metadata, another repository, expanded scope, deleted work, or shared-history force pushes.

## 1. Read, claim, and establish scope

Fetch complete issue context and relationships with `gh issue view`. Stop for a closed issue, strict blocker, or ambiguity. Restate acceptance criteria, explicit exclusions and user limits, and safety invariants. Resolve base. Record expected files, approximate hand-written diff, generated artifacts, risk, checks, mode, and root.

Treat file lists, diff estimates, and repair/retry counts as advisory, not approval gates. Do not invent caps or encode estimates as hard limits in goals, plans, or handoffs. Honor explicit user limits and existing safety policy.

In standalone mode assign `@me`, resolve the delivery project from native relationships or policy, set exact `In Progress`, apply only supported metadata, and verify issue state.

## 2. Isolate

Reuse an orchestrator-created worktree and branch exactly; otherwise create one from resolved base. Never nest or rename it. Only the recorded stack owner runs `gh stack rebase`, `submit`, or `sync`. Stop on remote movement or conflicting checkout ownership.

## 3. Implement the smallest correct diff

Implement only frozen criteria. Follow repository TDD and changelog rules. Run named acceptance and focused checks while editing.

Classify discoveries under `change-control`. Fix blocking and coupled findings needed for the authorized objective, including necessary additional files and tests. Update the plan as the implementation becomes clearer; do not ask approval solely for a larger diff or an initially unlisted file. Report unrelated findings without code changes. Stop for uncertain requirements or before entering an unauthorized repository, changing behavior outside the requested outcome, exceeding an explicit user limit, or taking an unapproved destructive action.

In delegated mode, finish the requested local commit and return here.

## 4. Freeze and review

Require a clean worktree and record base tip, merge-base, head/tree OIDs, exact diff, and surface totals.

- **Low:** no independent review unless policy requires one.
- **Medium:** one focused review containing relevant correctness, test, and abstraction lenses.
- **High:** one combined multi-angle review satisfying required safety and abstraction evidence.

Use `fess` only as a read-only lens when warranted. Do not invoke `fix-all` or `wiggum`. Leaf reviewers return evidence and never repair or dispatch.

Validate and classify findings. The root continues fixing blocking and coupled findings until the authorized acceptance criteria and required gates pass, unless a genuine blocker requires user input. After repair, rerun affected checks and only invalidated review concerns. Repeat broad review only after material behavior, architecture, risk, or target change.

## 5. Authoritative gate

Run focused checks during edits, then the repository-required full gate once on the final candidate. Repeat only after later material code change. If a failure repeats without progress, investigate the cause and change approach rather than retrying blindly. Continue useful in-scope work; escalate only a genuine blocker or a reached explicit user limit, not a retry count. Retain safe live evidence when explicitly required.

## 6. Draft PR

Commit with why and no AI attribution. Use `pr-description` as a leaf with the frozen issue, diff, checks, review packet, risk, explicit user limits, and live evidence. It consumes caller evidence rather than dispatching duplicate gates.

Push explicitly and create a draft against resolved base. Assign `@me`, apply supported labels, include `Closes #<N>`, and verify live base/body.

## 7. CI and Bugbot

Classify before editing. Continue fixing blocking or coupled failures/findings, run affected checks, amend, and push safely. Reassess repeated failures without progress and report genuine blockers; do not stop merely because additional repair rounds are needed. Report unrelated findings. Material repairs invalidate only relevant evidence; formatting, body, and evidence-only changes do not restart gates. Refresh the body only when implementation or evidence changed, preserving a trailing Bugbot summary.

## 8. Handoff

Verify base ancestry, clean worktree, green latest SHA, and no blocking findings. Preserve the tree during any required history cleanup and use an explicit lease. Mark ready. Report PR/base/SHA, risk, expected versus actual surface, repair rounds, reviews/subagents, gates, dispositions, explicit user limits, genuine blockers, issue hygiene, and open decisions. Never merge.
