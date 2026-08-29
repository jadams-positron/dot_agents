---
name: change-control
description: >-
  Apply the shared bounded-change contract by freezing scope and risk, pursuing
  the smallest correct diff, keeping one root orchestrator, classifying
  findings, deduplicating gates, and stopping before material expansion.
---

# Change Control

Optimize in this order: smallest correct diff; risk-proportionate rigor; one authoritative gate per concern; stable scope; bounded execution; one root orchestrator with leaf children; stable-candidate review; blocking/coupled finding repair; change-budget awareness; focused then final tests; human control at expansion; cost evidence.

Correctness, repository safety rules, and acceptance criteria remain hard floors. Budget exhaustion means stop and escalate, never skip a required check.

## Freeze

Before editing, record acceptance criteria and safety invariants, base/head, expected files and approximate hand-written diff, generated artifacts, risk tier, authoritative gates, root orchestrator, and delegated leaves.

- **Low:** narrow local or documentation change without contract or safety impact. Focused checks and required final gate; no reviewer or subagent unless policy requires one.
- **Medium:** observable behavior or public-contract change. Add a proving test, focused checks, and one relevant review.
- **High:** security, persistence, concurrency, deployment, migration, destructive behavior, or broad architecture. Complete gate and one combined independent review containing required specialist lenses.

Risk changes evidence depth, not scope.

## One orchestrator

Exactly one root owns budgets, dispatch, retries, repairs, commits, pushes, CI, and completion. A child skill is a leaf: perform one supplied inspect, draft, validate, or implementation operation and return evidence. A leaf does not invoke an orchestrator, dispatch, repair its own findings, or restart the caller. A normally top-level workflow used beneath a root must use delegated mode and return before orchestration.

## Findings

Classify every discovery:

- **Blocking:** acceptance, correctness, safety, or required gate cannot pass; fix within scope.
- **Coupled:** requested work cannot reasonably complete without it; fix and account for budget.
- **Unrelated:** separable; report without changing code.
- **Uncertain:** ambiguous scope or intent; stop before expansion.

Discovery is not authorization. Stop before crossing a repository, subsystem, public behavior boundary, or declared file set.

## Bounds and convergence

Defaults unless stricter policy applies:

- at most two total repair rounds;
- at most three attempts for the same failure without progress;
- one broad review of one frozen candidate;
- one authoritative full gate, repeated only after later material change;
- no subagents for low risk;
- at most one reviewable subagent wave for medium risk.

Compare actual surface with the estimate after implementation and each repair. Stop for undeclared files, another repository, a new subsystem, or materially larger scope.

Run focused tests while editing. Freeze before broad review. After repair, rerun affected checks and only invalidated review concerns. Repeat broad review only after material behavior, architecture, risk, or target change.

## Report

Report expected and actual surface, risk, repair rounds, review and subagent counts, focused and full gates, finding dispositions, and every scope or budget crossing.
