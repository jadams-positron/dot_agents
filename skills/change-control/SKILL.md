---
name: change-control
description: >-
  Use when planning or implementing code changes, classifying findings,
  coordinating root and leaf work, or deciding whether additional files,
  a larger diff, or further repairs require user approval.
---

# Change Control

Optimize in this order: smallest correct diff; risk-proportionate rigor; one authoritative gate per concern; stable user-authorized scope; one root orchestrator with leaf children; stable-candidate review; blocking/coupled finding repair; focused then final tests; human control over actual scope changes; cost evidence.

Correctness, repository safety rules, and acceptance criteria remain hard floors. Never skip a required check to fit an estimate.

## Scope and estimates

Before editing, record acceptance criteria, explicit exclusions and user limits, authorized repositories, safety invariants, base/head, expected files, generated artifacts, risk tier, authoritative gates, root orchestrator, and delegated leaves.

File lists, approximate hand-written diff sizes, and repair/retry counts are planning information, not approval gates. Do not invent hard caps or turn estimates into permission limits in a goal, plan, or handoff. Continue necessary implementation, coupled fixes, and verification within the authorized objective without asking permission merely because more lines, files, tests, or repair rounds are needed. Update estimates as understanding improves.

Honor explicit user limits and genuine tool/resource limits. Stop and explain the blocker when further progress requires new authorization, access, an unavailable resource, or a missing user decision—not merely a larger implementation than estimated.

- **Low:** narrow local or documentation change without contract or safety impact. Focused checks and required final gate; no reviewer or subagent unless policy requires one.
- **Medium:** observable behavior or public-contract change. Add a proving test, focused checks, and one relevant review.
- **High:** security, persistence, concurrency, deployment, migration, destructive behavior, or broad architecture. Complete gate and one combined independent review containing required specialist lenses.

Risk changes evidence depth, not scope.

## One orchestrator

Exactly one root owns scope, explicit user limits, dispatch, retries, repairs, commits, pushes, CI, and completion. A child skill is a leaf: perform one supplied inspect, draft, validate, or implementation operation and return evidence. A leaf does not invoke an orchestrator, dispatch, repair its own findings, or restart the caller. A normally top-level workflow used beneath a root must use delegated mode and return before orchestration.

## Findings

Classify every discovery:

- **Blocking:** acceptance, correctness, safety, or required gate cannot pass; fix within scope.
- **Coupled:** requested work cannot reasonably complete without it; fix within the authorized objective.
- **Unrelated:** separable; report without changing code.
- **Uncertain:** ambiguous scope or intent; stop before expansion.

Discovery is not authorization. Stop before changing the requested outcome, violating an explicit exclusion, entering an unauthorized repository, or taking an unapproved destructive action. A necessary change to another file or subsystem within the authorized objective is not itself scope expansion.

## Convergence

Continue in-scope repairs while evidence supports useful next steps. When failures repeat without progress, reassess the hypothesis, gather new evidence, or change approach rather than repeating unchanged attempts. Escalate genuine blockers; do not stop solely because a repair or retry counter reached an agent-chosen number.

Use these defaults to avoid redundant work:
- one broad review of one frozen candidate;
- one authoritative full gate, repeated only after later material change;
- no subagents for low risk;
- prefer one coordinated, reviewable subagent wave for medium risk.

Compare actual surface with the estimate after implementation and each repair to identify unnecessary changes and update the plan, not to request permission for required in-scope work. For example, an agent-estimated 1,000-line diff growing to 1,200 lines with a necessary new test file is not a blocker; an explicit user-imposed 1,000-line cap still is.

Run focused tests while editing. Freeze before broad review. After repair, rerun affected checks and only invalidated review concerns. Repeat broad review only after material behavior, architecture, risk, or target change.

## Report

Report expected and actual surface with reasons for material differences, risk, repair rounds, review and subagent counts, focused and full gates, finding dispositions, explicit user limits, and genuine blockers.
