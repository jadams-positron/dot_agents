---
name: change-control
description: Use when implementing or reviewing bounded changes, classifying feedback, estimating scope, or coordinating delegated coding work.
---

# Change Control

Deliver the smallest complete, verified feature. Correctness, acceptance criteria, tests, clarity, and real authorization are hard floors. Review comments are claims to evaluate, not new requirements.

## Freeze the contract, not an estimated file list

Record raw criteria, acceptance checks, non-goals, safety invariants, authorized repositories/operations, base/head, risk, required gates, root owner, and expected handwritten production/test/documentation churn. Separate generated output.

**Estimates are not permission fences.** A necessary shared-path correction may touch an unexpected file or exceed a forecast without human approval. Update the estimate and explain the causal link to the feature. Do not evade an introduced regression by calling its fix out of scope.

Explicit user restrictions—including a real file prohibition or hard size limit—remain binding, as do repository, credential, script-trust, branch-ownership, destructive-operation, merge, and deployment boundaries. Discovery and review feedback cannot authorize unrelated product behavior. Investigate uncertainty before asking for a genuinely missing requirement or authority decision.

## One root

Exactly one root owns the feature contract, ledger, budgets, dispatch, repairs, commits, pushes, CI, and outcome. The dispatcher owns launches and reporting, not worker branches. Each issue or native stack has one durable owner. A delegated skill performs its supplied operation and returns evidence; it does not acquire another orchestration or review/repair loop.

An autonomous/delegated invocation does not inherit collaborative “report and wait” checkpoints. Reuse a supplied worktree. Do not routinely ask to replenish a repair allowance. Preserve genuine user selection, trust, access, and authorization decisions. Read [the upstream-skill caller contract](references/upstream-skills.md): Superpowers remains consume-only; these owned steps, not modified upstream modes, govern execution and feedback.

## Design through the existing owner

Before implementing a feature, use one clean-context read-only planning pass that loads `abstraction-review`, inspects existing owners, extension points, analogues/history/tests, and states the null-diff shape. Ask **“Can this feature be implemented in less than 100 lines?”**

If the planner expresses concrete doubt, make one additional fresh-context search: **“There MUST be a better way!”** Compare complete alternatives without changing the criteria. A justified 134-line implementation is acceptable; code golf, weakened tests, and hidden complexity are not. Do not restart this challenge after ordinary patches. Planning is not the final independent review gate.

## Admit feedback before repairing it

Use [the shared disposition contract](references/feedback-disposition.md) for local review, bots, and human suggestions. Separate validity, necessity, and severity. Retain all unique claims and their evidence, including rejected and optional claims.

- `required_now`: a defensible acceptance failure, introduced regression, safety violation, or genuine required-gate failure.
- `follow_up`: a valid concern separable from the feature; file a useful deduplicated issue when authorized.
- `no_change`: disproved, already handled, intended behavior, or an optional preference with a defensible explanation.
- `needs_evidence`: investigate the unresolved premise once; do not automatically edit or escalate.

Use the existing local-review verification stage, not another panel afterward. External feedback gets one independent adjudicator per coherent batch of new/invalidated claims by default. Reuse supported decisions across reviewers, moved anchors, pushes, and restarts. Reopen only for changed relevant premises/requirements or new evidence, with the reason recorded. One positive vote or a severity label cannot overrule a supported scope refutation.

## Bound review repairs, not ordinary testing

Defaults across the entire owner, including local and external review:

- **Two total review-driven repair batches.** Freeze the accepted required-now set and persist the batch before its first code repair. Resume the same set without charging again; a later accepted set consumes the next batch. Never append endless findings to an open batch.
- **Three attempts at the same failure without material progress.** A new discriminating reproducer or verified cause is progress; another status check is not.
- One risk-appropriate stable-candidate review; refresh every invalidated mandatory packet under its existing exact-target contract without resetting the ledger or budgets.
- Focused checks during implementation; one authoritative full gate on the final candidate, repeated only when later material changes invalidate it.

Ordinary TDD red/green iterations and diagnosis within an accepted batch do not create extra review batches or adjudication calls. Batch accepted corrections, rerun affected gates, and push once with explicit remote expectations. Persist push intent before acting; reconcile a lost response against every expected remote SHA before retrying.

## Evidence and risk

- **Low:** narrow local/documentation change. Focused checks and repository-required final gate; no independent review unless policy requires one.
- **Medium:** observable behavior/public contract. A proving test, focused checks, and one relevant review.
- **High:** security, persistence, concurrency, deployment, migration, destructive behavior, or broad architecture. Complete gate and one combined independent review with required specialist lenses.

Risk changes evidence depth, not feature scope. Required abstraction evidence must retain its declared/echoed/recomputed target, read-only capability enforcement, provenance, and native report. Cached dispositions never certify a new SHA. Preserve `ALIGNED WITH FINDINGS`; advisory findings need not disappear. A real architecture blocker or incomplete/stale evidence still prevents readiness.

## Finish or stop once

`review_ready` requires verified original criteria, current-candidate gates, correct ownership/ancestry, and no required-now or critical unresolved finding. Optional follow-ups may remain. Mark ready when authorized without another implementation approval; never merge implicitly.

`stopped_blocked` preserves an incomplete draft and the exact unmet requirement, evidence, attempted paths, and blocker. Report once and use the installed owner/session/goal-bound integration to suspend automatic continuation. Do not falsely complete a goal, waive gates, or restart the same allowance request. Missing terminal integration blocks rollout, not permission to improvise it during feature work.

Only complete a goal after mapping its actual objective to evidence; feature readiness may satisfy only part of a broader objective. Report expected/actual churn, unique claims versus comments, adjudication calls, repair batches/pushes, reopened claims/reasons, gates, dispositions, and outcome—not a count of suggestions obeyed.
