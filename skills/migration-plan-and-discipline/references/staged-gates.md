# Staged Gates — Checkpoint Mechanics

Convergence is staged, not continuous. Each gate is a **checkpoint tag** on a
known-good state; the next gate does not open until the current one is green.
Tagging every gate makes rollback a `git checkout`, not an archaeology project.

```bash
git tag migration/gate-<name>    # after a gate goes green
git tag -l 'migration/gate-*'    # see how far the port has converged
```

Gate order: `translated` → `compile` → `smoke` → `ci` → `parity`.

## gate-translated

Every source unit has a corresponding target file, structure-preserving (one
file, same order, same names). Verify the denominator mechanically:

```bash
# counts must match the source unit count recorded at plan time
find src -name '*.py' | wc -l
find target -name '*.go' | wc -l
```

Also verify no `TODO` rows remain in `PORTING.md` or the decisions ledger. Do not
attempt to compile yet — translate everything first so compile errors are seen as
a population, not a trickle.

## gate-compile — batch by error class

Do **not** fix compile/type errors file-by-file top-to-bottom. Collect them all,
bucket by error class, and fix one class across every file in a batch. This
produces coherent, reviewable diffs and is exactly the shape `fix-all` parallelizes.

```bash
# collect and cluster: which error classes dominate?
go build ./... 2>&1 | sed -E 's/^[^:]+:[0-9]+:[0-9]+: //' | sort | uniq -c | sort -rn
# e.g. "undefined: X" (N), "cannot use ... as ... in argument" (M), "missing return" (K)
```

Fix the largest class first (one `fix-all` task per class), re-run the compiler,
re-cluster, repeat until zero. One commit per error class, message naming the
class. Tag `gate-compile` only when the build is clean with zero errors.

## gate-smoke

One real end-to-end path exercised against the new code — the thinnest slice that
proves the port is wired together (startup, one request/one job, shutdown). Not the
full suite. If smoke fails, the break is in wiring, not logic; fix before CI.

## gate-ci

Full test suite green on the target. Tests come from `test-census-parity` — the
ported test surface must equal the source's (no silently dropped cases). When a
regression appears, bisect over the per-unit commits (cheap because the port is
structure-preserving and one-change-per-commit):

```bash
git bisect start HEAD migration/gate-compile
git bisect run <the failing test command>
```

## gate-parity — wire the three parity skills

Green CI proves the new code is self-consistent, not that it matches the old.
Prove behavioral equivalence:

- `semantic-delta-catalog` — every enumerated source→target behavioral delta is
  burned down or explicitly accepted (documented, not silent).
- `test-census-parity` — before/after test-surface census shows no lost coverage.
- `differential-golden-harness` — old vs new outputs match across a representative
  corpus; investigate every diff.

Tag `gate-parity` only when all three report clean. This is the hand-off point to
`cutover-strangler-runbook` — the code is correct but not yet live.

## The labeled cleanup follow-up

Everything banned from the port (renames, dedup, re-layering, `unsafe`/`any`
reduction, perf rewrites, API improvements) is collected as it is encountered into
a backlog and executed **after cutover** on branches prefixed `cleanup/idiomatic-`.
Keeping these out of the port is what preserved diffability and bisect through
every gate above — do not relax it under schedule pressure.
