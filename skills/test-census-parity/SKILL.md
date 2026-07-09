---
name: test-census-parity
description: >-
  Use this skill before merging a refactor, migration, or port branch that
  claims behavior is unchanged, to mechanically prove it preserved its whole
  test surface. Inventories every test on the base ref and on HEAD, then fails
  on any silently deleted, renamed-away, skipped, xfail'd, short-guarded,
  build-tag-excluded, or assertion-weakened test, and compares a coverage floor.
  Triggers: "did we drop/skip any tests?", "is coverage the same?", "is this
  really behavior-preserving?", "did the rewrite lose test coverage?".
---

# Test Census Parity

## Overview

Refactor, migration, and port branches routinely claim "behavior unchanged" while silently shedding tests — a deleted file, a rename with no counterpart, a `t.Skip`, an `xfail`, a `testing.Short()` early-return, a table case dropped from a slice, an assertion commented out. This skill turns that prose claim into a mechanical merge gate: a before/after census of the test **surface** on the base ref versus HEAD that fails on any lost or weakened test and on any coverage regression. It measures the tests, not the code, and generalizes to any refactor — not just cross-language migrations.

## When to use

- Before merging any refactor/migration/port branch that asserts behavior is unchanged; when asked "did we drop or skip any tests?", "is coverage the same?", "is this really behavior-preserving?".
- As the test-surface gate invoked by `migration-plan-and-discipline`. Pair it with `semantic-delta-catalog` (source→target behavioral deltas) and `differential-golden-harness` (old-vs-new output diffing) for full migration coverage — this skill answers "are the same tests still here and still real?", not "do the two implementations agree?".
- When the census finds a genuinely dropped or gutted test, hand the repair to `fix-all` (it restores/re-expresses the test upstream). This skill only *detects*; it does not lower the bar.
- NOT for greenfield or net-new-feature branches — there is no base surface to preserve, so use `fix-all` to author tests for new code. NOT a qualitative review (`agent-pr-review`, `review-pr`); those judge quality, this one counts. NOT an output-equivalence check (`differential-golden-harness`).

## Workflow

1. **Pin the two refs.** Base is the merge-base with the target branch, HEAD is the branch tip:
   ```bash
   BASE=$(git merge-base origin/<target-branch> HEAD); HEAD_SHA=$(git rev-parse HEAD)
   ```
   Materialize the base in a throwaway worktree so both trees exist side by side (work in a scratch worktree; never stash or switch the shared checkout):
   ```bash
   git worktree add -d /tmp/parity-base "$BASE"
   ```
   Remove it at the end with `git worktree remove --force /tmp/parity-base`.

2. **Inventory both surfaces.** Run the census one-liners from `references/census-commands.md` in each tree, writing sorted, package-qualified artifacts (`base.tests`/`head.tests`) plus the count files (subtests, table cases, assertions, skips). The name list is the spine of the gate; the counts are corroborating signals.

3. **Diff the name inventory — the hard gate.** `comm -23 base.tests head.tests` lists every test on base absent from HEAD. Each is a **failure** unless it is (a) matched to a genuine rename/move — pair it with an added test of equivalent body via `git log --follow`, similarity, or the migration's decisions ledger — or (b) carries a `PARITY-ALLOW` (step 6). An unmatched removal is never waved through silently.

4. **Hunt new skips and weakenings.** Grep both trees for the skip/xfail/short-guard/build-tag/commented-assert markers in `references/census-commands.md` and diff the counts. Any marker present on HEAD but not on base is a finding — a formerly-running test that HEAD quietly disarms counts the same as a deleted one.

5. **Compare assertion density and coverage.** Equal test names with fewer assertions means a test was hollowed out — flag any per-package drop. Then run the coverage floor in both trees and diff per package; any package whose coverage falls is a finding. Record the exact commands and numbers.

6. **Adjudicate via `PARITY-ALLOW`.** The only sanctioned escape hatch for an intentional removal, skip, or coverage drop is a `PARITY-ALLOW <reason>` annotation stating why the behavior it covered no longer exists — placed in the commit message, the PR body, or an inline comment at the deletion site. Grep for it (recipe in the reference) and subtract matched removals from the findings. Anything unannotated stays a failure.

7. **Emit the report and set the gate** (below).

## Gate

FAIL if any of these survive adjudication:
- a base test name missing from HEAD with no matched rename and no `PARITY-ALLOW`;
- a new skip / `xfail` / `testing.Short()` guard / excluding build tag / commented-out assert on HEAD;
- a per-package assertion-count or coverage drop.

PASS only when the removed-set is empty after `PARITY-ALLOW` subtraction, no new weakenings exist, and coverage holds per package. Report the pass explicitly with the numbers — a green with no census run is not a pass.

## Report

Emit a compact report: the two refs; test-name counts (base / HEAD / removed / added / renamed-matched); the removed-without-allow list (the blocking findings); new-weakening markers with file:line; the per-package assertion and coverage deltas; and every `PARITY-ALLOW` with its reason. Close with the gate verdict. Hand blocking findings to `fix-all` for repair.

## References

- `references/census-commands.md` — exact Go and Python census one-liners (test-name enumeration, subtest/table/assertion counts), the base-vs-HEAD diff recipe, the skip/weakening grep patterns, the coverage-floor commands, and the `PARITY-ALLOW` grep.
