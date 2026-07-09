---
name: migration-worthiness-memo
description: Produce a go/no-go memo deciding WHETHER a large migration or rewrite is worth doing, before any code is written. Use when someone asks "should we rewrite X in Y?", "is it worth migrating to Z?", "port this service to another language?", or proposes a big-bang rewrite. Mines the repo's failure history to enumerate the bug classes the current stack structurally ALLOWS, classifies each as eliminated-at-compile-time (STRONG) vs merely perf/taste/ecosystem (WEAK) by the target, quantifies the do-nothing cost and a rough AI-effort/token budget, sets explicit kill criteria, and recommends GO / NO-GO / DEFER. On GO, hands off to `migration-plan-and-discipline`.
---

# Migration Worthiness Memo

## Overview

Decide *whether* to migrate before writing a line of the port. Every sibling
skill assumes the work is already chosen; this one prevents an unjustified
rewrite. The thesis: a large migration is justified only when the target
**converts recurring bug classes into compile errors or makes them unrepresentable
by construction** — not because the target is faster, more fashionable, or more
to taste. The output is a one-page memo grounded in the repo's own failure
history, ending in a GO / NO-GO / DEFER recommendation.

## When to use

- A proposal to rewrite/port a service, library, or component in another
  language, framework, or runtime ("rewrite X in Rust", "port this to Go",
  "move off the ORM").
- Any "is it worth migrating to Z?" question where no code has been written yet.
- **Not** for already-approved migrations, or once execution has begun — go
  straight to `migration-plan-and-discipline`.
- **Not** for small in-language refactors or dependency bumps — those don't
  need a worthiness memo.
- On a **GO** verdict, hand off to `migration-plan-and-discipline` (which owns
  PORTING.md, staged gates, and delegates execution to `fix-all`).

## Workflow

1. **Frame the proposal.** Record source stack → target stack, the unit being
   migrated (whole service? one module?), the date, and the *stated* motivation
   verbatim. If the motivation is vibes-only ("cleaner", "everyone uses Y"),
   note it — the memo must replace it with evidence.

2. **Mine the failure history.** Enumerate concrete past failures from every
   available source. Real starting commands (tune the window, e.g. 18 months):
   ```bash
   git log --since='18 months ago' -i --oneline \
     --grep='fix\|bug\|panic\|crash\|npe\|nil\|null\|race\|leak\|overflow\|timeout\|regression'
   gh issue list --label bug --state all --limit 500 --json number,title,closedAt,labels
   gh pr list --search 'label:bug is:merged' --state merged --limit 500 --json number,title
   rg -il 'postmortem|incident|root cause|RCA|retro' docs/ runbooks/ 2>/dev/null
   ```
   Also scan the CHANGELOG's "Fixed" entries and any incident tracker. Capture
   each failure with a link — this is the memo's evidence base.

3. **Enumerate bug CLASSES.** Bucket the mined failures into structural
   *classes*, not individual bugs. A class is a category the current stack's
   design *allows by construction* (e.g. manual-lifetime use-after-free,
   untyped-config drift, nil/null deref, stringly-typed errors, non-exhaustive
   switch, data race on shared state). See
   `references/bug-class-catalog.md` for the catalog and how to bucket.

4. **Classify each class STRONG vs WEAK against the target.** For every class
   ask: does the target eliminate it *at compile time or make it
   unrepresentable*? If yes → STRONG. If the target only helps marginally
   (perf, idiom/taste, library ecosystem, hiring) → WEAK. Use the heuristics and
   worked source→target mappings in `references/bug-class-catalog.md`.

5. **Quantify the do-nothing cost.** For the STRONG classes, tally the recurring
   toll from step 2: bug rate per quarter, incident/on-call hours, revert count,
   customer impact. This is what the migration buys back.

6. **Estimate the AI-effort budget.** Size the port: units/LOC to translate
   (`tokei`/`cloc`), the test surface that must reach parity (feed this to
   `test-census-parity` later), and a rough token/time/cost range for
   AI-driven translation + review. Compare against the multi-year do-nothing cost.

7. **Define kill criteria.** Write explicit, checkable conditions under which the
   migration is *abandoned mid-flight* (e.g. "differential harness can't reach
   parity on corpus after N units", "target can't express constraint C without
   `unsafe`/escape hatch", "budget burns past 2× estimate at <30% units done").
   A migration with no definable kill criteria has unbounded blast radius → NO-GO.

8. **Write the memo.** Fill `references/memo-template.md` and deliver the
   recommendation.

## Gate — the GO / NO-GO rule

- **GO** only when the bug classes that dominate the do-nothing cost (top by
  frequency × severity) are **STRONG**, kill criteria are definable, and the
  effort budget is justified by the multi-year do-nothing cost. Hand off to
  `migration-plan-and-discipline`.
- **NO-GO / DEFER** when the strongest motivations are **WEAK** (perf, taste,
  ecosystem — address those in-language), when no kill criteria can be written,
  or when the budget dwarfs the recurring cost it removes.

## Output

A one-page memo (from the template): proposal header, the bug-class table with a
STRONG/WEAK verdict column, do-nothing cost, effort budget, kill criteria, and a
single-line GO / NO-GO / DEFER recommendation with rationale and next step.

## References

- `references/memo-template.md` — the fillable one-page memo skeleton.
- `references/bug-class-catalog.md` — common structural bug classes, the
  STRONG-vs-WEAK heuristic, and worked source→target mappings.
