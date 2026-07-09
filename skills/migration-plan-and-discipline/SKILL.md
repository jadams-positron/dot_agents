---
name: migration-plan-and-discipline
description: >-
  Plan and enforce a large mechanical migration after a go/no-go decision is
  already made: synthesize a PORTING.md translation guide and a cross-cutting
  decisions ledger, mandate structure-preserving one-source-file-to-one-target-file
  translation (idiomatic cleanup banned to a labeled follow-up), and converge
  through checkpointed staged gates — all-translated, compile/type-clean, smoke,
  full CI, then parity. Triggers on "port X to Y", "migrate this package/service
  to <language/framework>", "convert every handler/model/repo to the new pattern",
  "rewrite this in Go/Rust/TypeScript". Delegates mechanical execution to `fix-all`,
  per-unit review to `agent-pr-review`, wires parity gates to `semantic-delta-catalog`,
  `test-census-parity`, and `differential-golden-harness`, and hands the live
  cutover to `cutover-strangler-runbook`.
---

# Migration Plan & Discipline

## Overview

The hub for the plan-and-execute phase of a large mechanical migration. It exists to keep a multi-week, multi-file port **diffable, bisectable, and reviewable** instead of collapsing into an untraceable rewrite. It produces two durable artifacts (a translation guide and a decisions ledger), imposes one hard rule (translate structure first, clean up later), and drives convergence through gates that must go green in order. Mechanical execution, review, and parity checks are delegated to sibling skills; this skill owns the plan, the discipline, and the checkpoints.

## When to use

- After a GO decision (`migration-worthiness-memo`) on "port X to Y", "migrate this service to <framework>", "rewrite this package in <language>", "convert every handler/model to the new pattern".
- When the change is **mechanical and repetitive across many units** — the value is consistency, not creativity.
- **Not** when there is no explicit go decision yet → run `migration-worthiness-memo` first.
- **Not** for a single in-language refactor of one file → just do it (optionally `fix-all`).
- **Not** for shifting live traffic onto the new implementation → that is `cutover-strangler-runbook`.

## Workflow

1. **Confirm GO and freeze the source.** Require the worthiness memo's decision. Tag the source at a fixed commit (`git tag migration/source-base`) so it cannot drift under the port; land any further source changes on both sides deliberately. Enumerate the translation units (one target file per source file) and record the count — it is the denominator for every gate.

2. **Synthesize `PORTING.md`.** Copy `references/porting-md-template.md`. Discover the recurring source idioms mechanically (`rg`, `ast-grep --lang <src> -p '<pattern>'`) — collections, error handling, null/optional, iteration, resource cleanup, concurrency, serialization. One table row per idiom: *source idiom → target idiom → rule → ONE worked before/after example*. The guide is the single source of truth every unit must follow.

3. **Synthesize the decisions ledger** (the cross-cutting judgment calls). Copy `references/decisions-ledger.tsv`. One row per module/object capturing what must be consistent everywhere: ownership (who allocates / frees / closes), nil-vs-zero-value policy, error-wrapping convention, concurrency model, and logging. Resolve each call once, here — not per file, not by whoever touches it.

4. **Mandate structure-preserving translation.** One source file → one target file, **same declaration order, same names**. Idiomatic cleanup, dedup, re-layering, and unsafe/`any`-reduction are **banned** from the port and deferred to a separate, labeled follow-up (see `references/staged-gates.md`). This is what keeps the diff readable and `git bisect` meaningful. State this rule verbatim to every executor.

5. **Delegate execution and review.** Fan the units out with `fix-all` (parallel subagents in `git worktree`s, one test per changed unit). Route each translated unit through `agent-pr-review` for per-unit adversarial review before it counts as done. Pass PORTING.md + the ledger into every delegated task so subagents share the conventions.

6. **Converge through staged gates** (details + commands in `references/staged-gates.md`). Each gate is a checkpoint tag; do not open the next until the current is green:
   `gate-translated` (every unit exists) → `gate-compile` (compile/type errors driven to zero, **batched by error class**) → `gate-smoke` (one end-to-end path) → `gate-ci` (full suite green) → `gate-parity`. Wire the parity gate to `semantic-delta-catalog` (behavioral deltas burned down), `test-census-parity` (no test surface dropped), and `differential-golden-harness` (old vs new outputs match over a corpus).

7. **Hand off the cutover.** Once `gate-parity` is green, the code is ready but not live. Hand runtime rollout, traffic shifting, and rollback to `cutover-strangler-runbook`. Only after cutover, schedule the labeled idiomatic-cleanup follow-up.

## Gate

Done for the plan-and-discipline phase means **all** hold:

- PORTING.md and the decisions ledger exist, are filled (no TODO rows), and are referenced by every executor.
- Unit count translated == source unit count; every unit passed `agent-pr-review`.
- All five gates are green and tagged, in order. `gate-compile` was reached by batching error classes, not one-off patches.
- Parity is proven, not assumed: the three parity skills report clean.
- Zero idiomatic-cleanup or unsafe-reduction commits landed inside the port; all are captured in the labeled follow-up.
- Cutover is handed to `cutover-strangler-runbook`.

## References

- `references/porting-md-template.md` — skeleton for PORTING.md: the idiom-mapping table, how to mine idioms, and the banned-cleanup list.
- `references/decisions-ledger.tsv` — skeleton TSV for the cross-cutting decisions ledger (ownership / nil-vs-zero / error-wrapping / concurrency / logging per module).
- `references/staged-gates.md` — the checkpoint mechanics: batching compile errors by class, `git bisect` over per-unit commits, smoke/CI/parity wiring, and the follow-up labeling convention.
