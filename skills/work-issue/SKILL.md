---
name: work-issue
description: Work one GitHub issue through a bounded, risk-proportionate implementation and review-ready PR. Freeze acceptance criteria and a change budget, produce the smallest correct diff, use one root orchestrator and one stable-candidate review, run focused checks plus the required final gate, and stop before material expansion. Merge is never part of the flow.
---

# Work Issue

Drive one issue to a review-ready PR under `change-control`. The human merges.

## Modes

In **standalone mode**, this is the sole root orchestrator and owns budgets, dispatch, repairs, commits, reviews, pushes, CI, and PR state.

Use **delegated mode** only when an outer workflow names itself as root. Read the issue, implement the frozen bounded unit, run focused checks, create the requested local commit when authorized, and return candidate evidence. Do not dispatch, broadly review, push, open a PR, handle CI, retry orchestration gates, or modify scope. Stack members use delegated mode; the stack owner is root.

## Authorization

Standalone invocation authorizes assigning `@me`, setting an unambiguous delivery project to `In Progress`, issue-branch commits, explicit-refspec pushes, a draft PR, ready state, and resolved review threads. It does not authorize merge, invented metadata, another repository, expanded scope, deleted work, or shared-history force pushes.

## 1. Read, claim, and freeze

Fetch complete issue context and relationships with `gh issue view`. Stop for a closed issue, strict blocker, or ambiguity. Restate acceptance criteria and safety invariants. Resolve base. Record expected files, approximate hand-written diff, generated artifacts, risk, checks, mode, root, and default budgets.

In standalone mode assign `@me`, resolve the delivery project from native relationships or policy, set exact `In Progress`, apply only supported metadata, and verify issue state.

## 2. Isolate

Reuse an orchestrator-created worktree and branch exactly; otherwise create one from resolved base. Never nest or rename it. Only the recorded stack owner runs `gh stack rebase`, `submit`, or `sync`. Stop on remote movement or conflicting checkout ownership.

## 3. Implement the smallest correct diff

Implement only frozen criteria. Follow repository TDD and changelog rules. Run named acceptance and focused checks while editing.

Classify discoveries under `change-control`. Fix blocking and coupled findings within budget. Report unrelated findings without code changes. Stop before uncertain scope, another repository, a new subsystem, public-behavior expansion, undeclared files, or materially larger diff.

In delegated mode, finish the requested local commit and return here.

## 4. Freeze and review

Require a clean worktree and record base tip, merge-base, head/tree OIDs, exact diff, and surface totals.

- **Low:** no independent review unless policy requires one.
- **Medium:** one focused review containing relevant correctness, test, and abstraction lenses.
- **High:** one combined multi-angle review satisfying required safety and abstraction evidence.

Use `fess` only as a read-only lens when warranted. Do not invoke `fix-all` or `wiggum`. Leaf reviewers return evidence and never repair or dispatch.

Validate and classify findings. The root fixes blocking and coupled findings. Permit at most two total repair rounds. After repair, rerun affected checks and only invalidated review concerns. Repeat broad review only after material behavior, architecture, risk, or target change.

## 5. Authoritative gate

Run focused checks during edits, then the repository-required full gate once on the final candidate. Repeat only after later material code change. Stop after three unchanged failures without progress; distinct failures still consume the two-round repair budget. Retain safe live evidence when explicitly required.

## 6. Draft PR

Commit with why and no AI attribution. Use `pr-description` as a leaf with the frozen issue, diff, checks, review packet, risk, budget, and live evidence. It consumes caller evidence rather than dispatching duplicate gates.

Push explicitly and create a draft against resolved base. Assign `@me`, apply supported labels, include `Closes #<N>`, and verify live base/body.

## 7. CI and Bugbot

Handle both within the same repair budget. Classify before editing. Fix only blocking or coupled failures/findings, run affected checks, amend, and push safely. Stop on three unchanged failures or exhausted total budget. Report unrelated findings. Material repairs invalidate only relevant evidence; formatting, body, and evidence-only changes do not restart gates. Refresh the body only when implementation or evidence changed, preserving a trailing Bugbot summary.

## 8. Handoff

Verify base ancestry, clean worktree, green latest SHA, and no blocking findings. Preserve the tree during any required history cleanup and use an explicit lease. Mark ready. Report PR/base/SHA, risk, expected versus actual surface, repair rounds, reviews/subagents, gates, dispositions, crossings, issue hygiene, and open decisions. Never merge.
