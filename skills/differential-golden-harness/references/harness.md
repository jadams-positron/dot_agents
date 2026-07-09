# Harness Mechanics

Concrete scaffolds for producing OLD vs NEW outputs, driving a corpus, diffing, freezing goldens, and triaging. Adapt paths and build commands to the project; nothing here is repo-specific.

## Producing the OLD baseline

Pick whichever reproduces the *released* behavior most faithfully:

- **Throwaway git worktree** (base ref still builds in-tree):
  ```bash
  git worktree add /tmp/base <base-ref>      # e.g. the pre-refactor tag/commit
  ( cd /tmp/base && <build> -o /tmp/old-bin )
  # ... run corpus ...
  git worktree remove /tmp/base
  ```
- **Prior released binary / artifact:** pull the shipped binary or container image and run it directly — best fidelity when the build is not reproducible from source.
- **Same-tree, two functions** (pure transform, both impls coexist): call `Old(x)` and `New(x)` in one process; no worktree needed.

## Environment pinning (both sides, identical)

Non-determinism starts at the environment. Export before every run:

| Var | Purpose |
|-----|---------|
| `TZ=UTC` | stable timestamps |
| `LC_ALL=C` / `LANG=C` | stable number/date/sort formatting |
| `NO_COLOR=1`, `TERM=dumb` | no ANSI |
| `PYTHONHASHSEED=0` | stable Python dict/set iteration |
| `SOURCE_DATE_EPOCH=<fixed>` | stable embedded build times |
| app seed flags | stable RNG |
| `GODEBUG` / disable jitter | remove runtime-timing surprises |

Freeze the clock where the code allows it (inject a fixed `now`), rather than masking timestamps after the fact.

## Corpus layout & driver

```
corpus/<id>.in         # one case per file (request body, argv, stdin, input value)
out-old/<id>           # captured OLD output (all contract channels)
out-new/<id>           # captured NEW output
```

CLI driver (captures stdout, stderr, exit code):
```bash
run() {  # run <bin> <outdir>
  for f in corpus/*.in; do id=$(basename "$f" .in)
    "$1" $(cat "$f") >"$2/$id.out" 2>"$2/$id.err"; echo $? >"$2/$id.code"
  done
}
run /tmp/old-bin out-old
run ./new-bin     out-new
```

- **HTTP handler:** replay a table of captured requests (method, path, headers, body) against each build via `httptest`/an in-process client; capture status + normalized headers + body per case.
- **Pure transform:** loop the corpus in one test, writing `Old(x)` and `New(x)` outputs; or assert equality directly in-process.

## Diffing

```bash
# text
diff -ru <(normalize out-old) <(normalize out-new)
# JSON, structural
for id in $(ls corpus | sed 's/.in//'); do
  diff <(jq -S . out-old/$id.out) <(jq -S . out-new/$id.out) && : || echo "DIFF $id"
done
```
Compare `*.code` (exit) / status exactly. Consider `jd`/`dyff` for readable structural JSON diffs. See `references/normalization.md` for the `normalize` step.

## Freezing the golden (generalize the project's convention)

The pattern to reproduce: golden fixtures under a `testdata/` dir + an `-update` flag that regenerates them + a `normalize()` applied before the equality assertion. Once frozen, the checked-in test fails on any future normalized-output drift, and regeneration is one flag.

Go:
```go
var update = flag.Bool("update", false, "regenerate golden files")

func TestParity(t *testing.T) {
    for _, c := range corpus(t) {
        got := normalize(New(c.in))
        golden := filepath.Join("testdata", c.id+".golden")
        if *update { os.WriteFile(golden, got, 0o644); continue }
        want, _ := os.ReadFile(golden)
        if !bytes.Equal(got, want) {
            t.Errorf("%s drift:\n%s", c.id, diff(want, got))
        }
    }
}
// regenerate: go test ./... -run TestParity -update
```

pytest:
```python
def test_parity(case, request):
    got = normalize(new_impl(case.input))
    golden = TESTDATA / f"{case.id}.golden"
    if request.config.getoption("--update"):
        golden.write_bytes(got); return
    assert got == golden.read_bytes()
# regenerate: pytest -k parity --update
```

Freeze the **normalized NEW** output only after triage confirms every diff vs OLD is intended — otherwise a regression becomes the golden.

## Triage table

Record one row per surviving normalized diff. Regressions go to `fix-all`; intended changes link to a `semantic-delta-catalog` entry.

| Case id | Channel / field | OLD | NEW | Verdict | Link / action |
|---------|-----------------|-----|-----|---------|---------------|
| user-empty | body `.error` | `"missing"` | `"required"` | intended | delta #DELTA-12 |
| list-50 | body `.items[]` order | sorted | unsorted | regression | fix-all: stabilize sort |
| big-arg | exit code | `0` | `2` | regression | fix-all: arg parsing |

## Handoffs

- Diffs classified as intended-but-unpinned → `semantic-delta-catalog` (record + pin the delta).
- Regressions → `fix-all` (fix upstream, add the test).
- The `normalize()` built here → hand to `cutover-strangler-runbook` for online shadow-compare (same normalizer, live traffic).
