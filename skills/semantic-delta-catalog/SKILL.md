---
name: semantic-delta-catalog
description: >-
  Use this skill when porting or rewriting code across a language, framework, or runtime version
  (Python to Go, Go 1.21 to 1.22, a framework major bump) and the risk is the "compiles fine but
  computes wrong" class of silent behavioral bug. Enumerates the source-to-target semantic deltas,
  sweeps the changed surface for each with grep/ast-grep, records every hit in a machine-readable
  burn-down catalog, and pins each hit with a targeted or differential test that fails under the
  wrong semantics. Triggers: "port X to Y", "rewrite this in Go", "audit the just-landed port for
  behavior change", "did the rewrite change behavior", "Go version bump", "runtime upgrade",
  "check for silent semantic differences".
---

# Semantic Delta Catalog

## Overview
A source-to-target port can pass typecheck and CI and still compute the wrong answer, because the two
languages/versions disagree on integer division sign, truthiness, map order, error propagation, nil,
numeric precision, and more. This skill turns that vague risk into a closed accounting task: load the
known deltas for the language/version pair, grep the changed surface for each construct, record every
hit in a catalog file, and pin each hit with a test that would FAIL under the wrong semantics. The
catalog is a migration gate — it is not done until every hit is tested or explicitly waived.

## When to use
- Starting, mid, or auditing a language/framework port (Python→Go, TS→Go, Python 2→3, etc.).
- A Go/runtime/framework version bump whose release notes changed behavior (loop var, time, GC of finalizers).
- As a gate invoked from `migration-plan-and-discipline` alongside `test-census-parity`.
- Hand off to `differential-golden-harness` when a delta is best pinned by diffing old-vs-new OUTPUT over a corpus rather than a unit assertion.
- Use `fix-all` to write the pinning tests at scale, and `test-census-parity` to prove no source test was silently dropped.
- NOT for pure additions/refactors within one language+version (no cross-semantics boundary), and not a substitute for a full test suite — it targets the delta surface only.

## Workflow
1. **Identify the pair and the surface.** Pin exact versions: read `go.mod` / `pyproject.toml` / lockfiles and `git log`. Compute the changed surface to sweep:
   `git diff --stat <base>..HEAD` and `git diff --name-only <base>..HEAD` (for a port, the target tree; for a version bump, the whole module).
2. **Load the delta table.** Read `references/language-deltas.md`. Take the matching starter set (Python→Go, or the Go-version/Go-to-Go set) as rows. Extend it for the specific surface — add project-specific constructs (custom numeric types, ORM truthiness, serializers) as new delta rows before sweeping.
3. **Run the census.** Copy `references/catalog-template.tsv` to a working `semantic-delta-catalog.tsv`. For each delta, run its grep/ast-grep pattern over the changed surface and record EVERY hit as a row (delta-id, construct, pattern, risk, location(s), pinning test, status=`hit`). Use `rg -n` for text patterns and `ast-grep -l <lang> -p '<pattern>'` for structural ones; triage noisy matches down to real occurrences. A delta with zero hits gets one row with status=`swept`.
4. **Pin each hit.** For every `hit` row, write a targeted unit test that asserts the SOURCE semantics and would fail under the naive target behavior (e.g. `-7/2 == -4`, empty-map write, int64 round-trip through JSON). For output-level or corpus checks, hand off to `differential-golden-harness` and reference its case id in the pinning-test column. Set status=`tested`.
5. **Waive with cause.** If a hit is provably safe (operands never negative, map never iterated for output, error intentionally dropped), set status=`waived` and put the one-line justification in the pinning-test column. Waivers are reviewable, not silent.
6. **Burn down and gate.** Re-run the sweep after edits (new code can introduce new hits). The catalog passes only when NO row is left in `hit`/`pending` — every row is `tested`, `waived`, `swept`, or `n/a`.

## Gate
The migration cannot advance past this gate while any catalog row has status `pending` or `hit`. Pass = every enumerated delta swept AND every hit either pinned by a failing-under-wrong-semantics test or explicitly waived with a one-line reason. Commit the final `semantic-delta-catalog.tsv` as the audit artifact; report counts by status and list every waiver.

## References
- `references/language-deltas.md` — Python→Go and Go-version/Go-to-Go delta sets; per delta: why it bites, a grep/ast-grep detection pattern, and a one-line pinning-test idea.
- `references/catalog-template.tsv` — the burn-down schema (delta-id, construct, pattern, risk, locations, pinning test, status) with the status vocabulary and example rows.
