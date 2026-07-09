---
name: differential-golden-harness
description: Diff the actual outputs of an old and a new implementation over an input corpus to prove byte-for-byte parity or triage every difference as intended-change vs regression, with a normalization pass that strips volatile timestamps, IDs, paths, color, and ordering. Use when verifying a ported endpoint, CLI, or pure transform produces the same output as the original ("does the new one produce the same output as the old one?", "is the rewrite byte-for-byte equivalent?"), characterizing legacy behavior before a risky refactor, or freezing a normalized golden fixture with an -update regeneration flag for ongoing regression protection.
---

# Differential Golden Harness

## Overview
Prove that a new implementation produces the same output as the old one — or triage every difference as intended-change vs regression — by running both over a shared input corpus and diffing normalized outputs. This is a characterization and parity tool: it captures legacy behavior as executable golden fixtures, useful before any risky refactor, not only during migrations. The load-bearing step is a normalization pass (strip volatile timestamps, IDs, absolute paths, ANSI color, non-deterministic ordering) so only meaningful differences survive the diff.

## When to use
- Verifying a ported endpoint, CLI, or pure transform is byte-for-byte equivalent to the original ("does the new one produce the same output as the old one?").
- Characterizing legacy behavior before a risky refactor and freezing it as a golden fixture.
- Invoked by `semantic-delta-catalog` to pin an output-level delta, and as an execution gate inside `migration-plan-and-discipline`; it supplies the normalizer that `cutover-strangler-runbook` reuses for online shadow-compare.
- NOT for perf, throughput, or race parity — use `investigate-performance`. NOT for driving a single flow end-to-end without diffing two implementations — use `verify`. To enumerate source-level behavioral deltas rather than output diffs, use `semantic-delta-catalog`; for test-surface parity, `test-census-parity`.

## Workflow
1. Define the output contract (the surface). Pick exactly one: CLI (stdout + stderr + exit code), an HTTP handler's response envelope (status + body + significant headers), or a pure transform (input value → output value). Write down every channel that counts as output; a channel omitted here is a channel that silently drifts.

2. Assemble the input corpus. Combine three sources into one case-per-file directory (`corpus/<id>.in`): real captured inputs (production request/log captures, sampled records), hand-written edge cases (empty, unicode, max size, null vs missing, malformed), and fuzz-generated cases (seed a fuzzer, cap sizes, dump the corpus). Bias toward inputs that exercise branches, not volume.

3. Produce OLD and NEW outputs over the identical corpus. Materialize OLD from the base ref via a throwaway `git worktree add` (or the prior released binary/artifact); build NEW from HEAD. Run each over every corpus case into `out-old/<id>` and `out-new/<id>`, capturing all contract channels. Pin the environment identically for both (`TZ=UTC`, `LC_ALL=C`, `NO_COLOR=1`, fixed seeds, `PYTHONHASHSEED=0`, `SOURCE_DATE_EPOCH`). See `references/harness.md`.

4. Normalize both sides identically. Apply the same normalizer to `out-old/` and `out-new/`, per output type, following `references/normalization.md`. Keep the raw outputs; normalize copies. Every rule must be symmetric and justified — over-normalization hides real regressions.

5. Diff normalized OLD vs NEW. For text: `diff -ru out-old-norm out-new-norm`. For JSON: canonicalize (`jq -S`) then diff, or use a structural differ. Compare exit/status codes exactly — never normalize them. A clean diff over a representative corpus is the parity claim.

6. Triage every surviving diff. Classify each into intended-change (a known, justified behavior change — link it to a `semantic-delta-catalog` entry) or regression. Record verdicts in the triage table (`references/harness.md`). Route regressions to `fix-all`; re-run steps 3–5 until only intended diffs remain.

7. (Optional, for ongoing protection) Freeze the normalized NEW output as a golden fixture. Generalize the project's golden-snapshot convention — golden fixtures under a `testdata/` dir plus an `-update` regeneration flag, with a `normalize()` pass applied before the equality assertion. Commit the golden; the checked-in test then fails on any future normalized-output drift, and regeneration is one flag. See `references/harness.md`.

## Gate
The parity gate passes only when, over a representative corpus, the normalized OLD/NEW diff contains **zero unexplained differences**: every diff is either eliminated (regression fixed upstream) or recorded as intended with a linked justification, and exit/status codes match exactly. A parity claim without a corpus that exercises the branches is not a pass — note corpus coverage explicitly. Freezing the normalized NEW output as a committed golden with an `-update` regen path (step 7) is optional for a one-shot parity check but required to keep the parity from silently rotting.

## References
- `references/normalization.md` — per-output-type checklist of what to strip and canonicalize (JSON, CLI text, logs), with concrete regexes, `jq`, and `sed` snippets, and the over-normalization caution.
- `references/harness.md` — old/new production mechanics (worktree, prior binary, env pinning), corpus layout, driver scaffolds (CLI, HTTP, pure transform), diff strategies, the generalized golden `-update` convention (Go + pytest), and the triage-table template.
