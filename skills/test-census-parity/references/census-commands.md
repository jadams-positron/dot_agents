# Census Commands

Exact one-liners for inventorying a test surface and diffing base against HEAD. Run every census command **twice** — once in the base worktree (`/tmp/parity-base`), once in HEAD — writing to `base.*` and `head.*` artifacts, then diff.

The **test-name list** is the hard gate (a name on base and gone from HEAD is a defect). The **counts** (subtests, table cases, assertions) are corroborating signals: a drop with the name list unchanged means a test was hollowed out rather than deleted.

All recipes assume `rg` (ripgrep). Swap `rg` for `grep -rE` if unavailable.

---

## Go

### Test-name enumeration (the spine)

`go test -list` prints only top-level `Test*`/`Benchmark*`/`Fuzz*`/`Example*` functions and appends `ok`/`?` status lines. Iterate packages so names are package-qualified (two packages may both define `TestFoo`):

```bash
for pkg in $(go list ./...); do
  go test -list '.*' "$pkg" 2>/dev/null \
    | rg '^(Test|Benchmark|Fuzz|Example)' \
    | sed "s#^#$pkg #"
done | sort -u > census.tests
```

Each line is `<import/path> <TestName>`. This is what `comm` diffs in the recipe below.

### Subtests and table-driven cases (signal, not spine)

`go test -list` cannot see `t.Run` subtests or table rows — enumerate them statically as counts. Dynamically-named subtests (`t.Run(tc.name, …)` in a loop) cannot be listed, so count both the `t.Run` call sites and the named table rows:

```bash
rg -o '\bt\.Run\(' -g '*_test.go' | wc -l           > census.subtests
rg -o '\bname:\s*"' -g '*_test.go' | wc -l           > census.tablecases   # heuristic: named struct rows
```

A shrinking `census.tablecases` with a stable `census.tests` is the classic "collapsed the table" weakening — investigate the specific table.

### Assertion density

```bash
rg -o 'require\.|assert\.|\bt\.(Error|Errorf|Fatal|Fatalf|Fail|FailNow)\b' -g '*_test.go' \
  | wc -l > census.asserts
```

For per-package density (to localize a drop), replace the pipeline with `rg -c … | ...` grouped by directory, or re-run scoped to each package dir.

---

## Python

### Test-name enumeration (the spine)

`pytest --collect-only -q` prints node IDs (`path::test_fn`, `path::Class::test_fn`, and one line per `@parametrize` case as `test_fn[param]`) plus a trailing summary line. Keep only node IDs:

```bash
pytest --collect-only -q 2>/dev/null | rg '::' | sort -u > census.tests
```

Parametrized cases appear as distinct IDs, so a dropped `@parametrize` value shows up here directly — no separate table count needed.

### Assertion density

```bash
rg -o '\bassert\b|pytest\.raises|self\.assert[A-Za-z]+' -g 'test_*.py' -g '*_test.py' \
  | wc -l > census.asserts
```

---

## Diff recipe (base vs HEAD)

With `base.tests` and `head.tests` produced by the enumeration commands above:

```bash
comm -23 base.tests head.tests > removed.tests   # on base, gone from HEAD  → BLOCKING
comm -13 base.tests head.tests > added.tests      # new on HEAD
comm -12 base.tests head.tests | wc -l            # survived unchanged
```

`removed.tests` is the finding set. Before failing, reconcile renames: for each removed name, look for a plausible counterpart in `added.tests` (same leaf test name in a moved package, or `git log --follow -- <old_test_file>`, or the migration decisions ledger). Genuine renames are fine; an unmatched removal is a failure unless `PARITY-ALLOW`'d.

Count deltas — any negative delta is a signal to chase:

```bash
paste base.asserts head.asserts        # assertion count: base vs HEAD
paste base.subtests head.subtests      # Go only
paste base.tablecases head.tablecases  # Go only
```

---

## Skip / weakening grep (new-on-HEAD only)

A test that HEAD quietly disarms counts the same as a deleted one. Grep both trees and diff — a marker present on HEAD and absent on base is the finding. Anchor findings with `-n` (`file:line`).

### Go

```bash
rg -n '\bt\.Skip(Now|f)?\(' -g '*_test.go'                 # skips
rg -n 'if\s+testing\.Short\(\)' -g '*_test.go'             # short-mode early return
rg -n '^//\s*(go:build|\+build)' -g '*_test.go'            # build-tag exclusions on test files
rg -n '^\s*//.*(require\.|assert\.|t\.(Error|Fatal))' -g '*_test.go'  # commented-out asserts
```

Also confirm no test file gained an exclusionary tag (e.g. `//go:build !ci`) or moved behind a tag the CI invocation does not pass — such files vanish from `go test ./...` without appearing in `removed.tests` unless the census is run with the same tags CI uses. Run the enumeration with the project's CI build tags (`go test -tags '<ci-tags>' -list …`) to catch this.

### Python

```bash
rg -n '@pytest\.mark\.(skip|skipif|xfail)' -g 'test_*.py' -g '*_test.py'
rg -n 'pytest\.skip\(|@unittest\.skip|unittest\.skip\(' -g 'test_*.py' -g '*_test.py'
rg -n '^\s*#\s*assert\b' -g 'test_*.py' -g '*_test.py'     # commented-out asserts
```

Diff base vs HEAD counts:

```bash
diff <(cd /tmp/parity-base && rg -c '@pytest\.mark\.(skip|xfail)' -g '*.py' | sort) \
     <(rg -c '@pytest\.mark\.(skip|xfail)' -g '*.py' | sort)
```

---

## Coverage floor

Run in both trees; compare per package/file. Any package whose coverage falls is a finding.

### Go

```bash
go test -cover ./... 2>/dev/null | rg 'coverage:' | sort > cover.by-pkg   # per-package %
go test -coverprofile=cover.out ./... >/dev/null 2>&1
go tool cover -func=cover.out | tail -1                                   # total %
```

Diff `base/cover.by-pkg` against `head/cover.by-pkg`.

### Python

```bash
pytest --cov --cov-report=term-missing 2>/dev/null | rg 'TOTAL|\.py'      # per-file + total
```

Capture in both trees and compare the `TOTAL` line and any file that regressed.

---

## PARITY-ALLOW escape hatch

The only sanctioned way to accept an intentional removal, skip, or coverage drop. Annotate the reason where the removal is defensible:

```
PARITY-ALLOW <reason the covered behavior no longer exists>
```

Valid locations: the commit message, the PR body, or an inline source comment at the deletion site. Collect them and subtract matched removals from the finding set:

```bash
{ git log "$BASE"..HEAD --format='%B'; git diff "$BASE"..HEAD; } \
  | rg -n 'PARITY-ALLOW\b.*'
```

An annotation must name the *behavior* that went away — "PARITY-ALLOW: dropped legacy XML codec, feature removed in #123", not "PARITY-ALLOW: refactor". A removal with no matching, behavior-justified annotation stays a failure.
