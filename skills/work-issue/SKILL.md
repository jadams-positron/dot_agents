---
name: work-issue
description: Use when asked to implement one GitHub issue and deliver a verified, review-ready PR, or a delegated member of a native PR stack.
---

# Work Issue

Deliver the smallest complete feature under `change-control`. The human merges. Read the shared policy, its feedback-disposition reference, and [the consume-only upstream caller contract](../change-control/references/upstream-skills.md). Do not reinterpret every review suggestion as acceptance criteria or invoke a conflicting upstream orchestration flow.

## Modes and authority

**Standalone:** act as this issue's sole root, owning its contract, ledger, planning/review dispatch, repairs, commits, pushes, CI, and outcome.

**Delegated:** an outer root supplies the feature contract, worktree, accepted unit, and remaining budgets. Implement, run focused checks, leave the requested local commit when authorized, and return evidence. Do not dispatch, broadly review, push, open PRs, handle CI, restart gates, or reset scope/budgets. A stack member is delegated; its stack owner alone orchestrates.

Invocation authorizes necessary in-feature implementation/corrections, proving tests, `@me` assignment, unambiguous project `In Progress` status, issue-branch commits and explicit-refspec pushes, draft PRs, supported labels/closing metadata, justified thread dispositions, and review-ready state. Useful deduplicated follow-up issues are authorized through repository `issue-templates`/`file-issue` conventions. Do not manufacture metadata or tickets for trivial preferences.

Preserve explicit user restrictions, credentials, script trust, repository boundaries, and shared-history ownership. No implicit merge, deploy, release, production-pin/protection changes, deleted user work, or new product scope. Estimated file lists and LoC are not prohibitions. Autonomous/delegated execution does not inherit routine wait-for-human checkpoints.

## 1. Read, claim, and freeze

Fetch the complete issue, comments, and native dependencies with `gh issue view`. Resolve genuine selection/requirements ambiguity and strict blockers. Freeze raw criteria, acceptance checks, non-goals, safety/authority boundaries, base, risk, expected handwritten surface, generated artifacts, and required gates.

Standalone owners assign `@me` and verify supported project/issue state. Do not invent a delivery project. Reuse an orchestrator-created branch/worktree exactly; otherwise create one from the resolved base. Never nest or rename it. Only the recorded stack owner may run `gh stack rebase`, `submit`, or `sync`.

For Agent Deck owners, use the versioned owner state protocol in `work-gh-issues` and its `references/owner-state.md`. Initialize only absent state; resume the same ledger, actual identities, expected SHAs, and counters after interruption. Parent dispatchers never edit owner ledgers or branches. Require compatible goal-terminal support before starting this workflow revision; do not auto-adopt an active legacy session or silently invent missing history.

## 2. Plan through the existing abstraction

The root performs the one clean-context `abstraction-review` planning pass required by `change-control`: existing owner, extension points, analogues/history/tests, null-diff shape, and **“Can this feature be implemented in less than 100 lines?”**

On concrete doubt, make one fresh **“There MUST be a better way!”** alternative search. Choose the smallest complete, clear solution without changing the criteria. A justified larger result is acceptable. This is not final review evidence. A delegated member returns planning questions to its root rather than dispatching another owner.

## 3. Implement and test locally

Use repository TDD/changelog conventions and the existing shared path. Iterate implementation → focused tests → diagnosis/correction locally. Two different test failures are not two review-driven repair batches.

Correct necessary in-feature behavior even in an unestimated file. Update the estimate and retain a useful reproducer. Record separable discoveries without implementing them. Investigate uncertain premises; ask only for a genuinely missing requirement, access, trust, or authority decision.

In delegated mode, finish the authorized coherent commit and return candidate/acceptance evidence here. Do not run a per-member broad review in addition to the aggregate stack review.

## 4. Freeze and review once

Finish necessary rebases, require a clean worktree, and freeze base tip, merge-base, head/tree OIDs, exact binary diff/digest, and surface totals. Apply the shared risk tier and repository-required review policy.

Use one stable-candidate review. Its existing verification stage adjudicates unique claims in batches under the shared disposition contract; do not append another panel. Give necessity judges the raw criteria. Keep native abstraction reports and all dispositions, including optional/no-change concerns. Leaves inspect and return; they never repair or dispatch.

Only defensible `required_now` findings enter the frozen repair set. Count at most two review-driven batches total for this owner, shared with external review. Persist the set before repairing; batch corrections and rerun affected checks. Recompute every invalidated mandatory canonical packet with its required fresh-context/capability/target contract, without resetting the ledger or inviting unrelated cleanup.

## 5. Gate and draft

Run the authoritative repository full gate on the final candidate; repeat only when later material changes invalidate it. Three attempts at the same failure without material progress are a separate backstop, not a quota on ordinary TDD iterations. Retain required safe live evidence.

Commit with why and required signing, without generated attribution. Give `pr-description` the exact immediate diff, criteria, observed checks/live evidence, native review packet, and explicit root readiness/dispositions. A leaf returns stale/missing evidence rather than rerunning the caller's gates. Nonblocking `ALIGNED WITH FINDINGS` stays native; real blockers and invalid provenance still stop readiness.

Persist the explicit push ref/expected remote SHA/new SHA before publishing. On a lost response, observe the remote instead of replaying history operations. Create a draft against the exact base; assign `@me`, apply supported labels, include `Closes #<N>`, and verify live base/body. Only the root performs publication.

## 6. Collect CI and external feedback

Collect completed required CI/reviewer runs for the current head with a persisted bounded deadline. Handle Bugbot, Droid, humans, and other configured sources through the same ledger, not separate loops. Missing required evidence is not success.

Reuse supported old dispositions. Only new evidence or changed relevant premises/requirements reopen a claim. Batch unique new/invalidated claims for one independent adjudicator; no agent or code push for repeated comments alone. Preserve rejected/optional concerns and deduplicate worthwhile follow-ups before filing.

If an accepted required-now set remains, use the owner's remaining repair batch, proving tests, affected gates, and one explicit-lease push. For stacks, only the stack root amends/rebases upstack and atomically syncs the chain; recheck every affected descendant at its latest SHA.

Refresh the PR body when implementation/evidence changes. Fetch the live body first, preserve its trailing Bugbot summary byte-for-byte, and validate with `--existing-body`. Body-only/evidence-only updates are not code-repair batches.

## 7. Finish or stop once

`review_ready` requires every original criterion verified, clean worktree, correct ancestry/ownership, latest required checks/reviews, complete current-target packets, and no required-now or critical unresolved finding. Optional suggestions do not require another implementation approval. Mark ready when authorized; never merge.

`stopped_blocked` preserves the incomplete draft and exact unmet criterion/evidence/attempts. Persist and report once. Use the bound terminal integration to pause automatic goal continuation while leaving the goal incomplete; do not waive gates or repeatedly request the same repair allowance. No associated goal means record that observation, not create one merely to pause it. Completion/idle/error notifications are only events to reconcile, not proof of success.

Complete an associated goal only after auditing its actual objective; this issue may satisfy only part of it. Report PR/base/latest SHA, criteria evidence, expected/actual surface, unique claims versus comments, dispositions/follow-ups, review/adjudication/repair counts, gates, and the honest outcome.
