# Language & Version Semantic Deltas

Behavioral differences that survive typecheck/compile and produce wrong output. Each delta gives: why
it bites, a detection pattern (`rg` for text, `ast-grep` for structure), and a one-line pinning-test
idea. Detection is deliberately over-broad — expect to triage matches down to real occurrences. Sweep
the SOURCE for the construct, then verify the TARGET site preserved semantics; target-side smells are
noted where they exist.

Extend these tables for the specific surface (custom numeric types, ORM/lazy truthiness, framework
serializers) before sweeping — add rows with new IDs.

---

## Python → Go

### PG-01 — Floor division `//` vs truncated integer `/` (and `%` sign)
**Why it bites:** Python `//` floors toward −∞ and `%` takes the divisor's sign; Go integer `/`
truncates toward zero and `%` takes the dividend's sign. `-7 // 2 == -4` (Py) but `-7 / 2 == -3` (Go);
`-7 % 3 == 2` (Py) but `-7 % 3 == -1` (Go). Silent whenever an operand can be negative.
**Detect:** `ast-grep -l python -p '$A // $B'`; source `%` on ints; target `ast-grep -l go -p '$A / $B'` and `$A % $B` (triage to int operands that can be negative).
**Test idea:** Assert quotient and remainder for a negative numerator match Python floor/modulo (`-7,2 → -4,1`).

### PG-02 — Arbitrary-precision int vs int64 overflow
**Why it bites:** Python ints are unbounded; Go `int`/`int64` wrap silently on overflow — no panic. Bites
factorials, hash/checksum accumulation, bit shifts, large products, monotonic counters.
**Detect:** `rg -n '<<|\*=|\+=|\*'` in hot/accumulation loops; source `**` or big multiplications; audit target `int64` accumulators fed by unbounded input.
**Test idea:** Feed an input that overflows int64 and assert the code errors or uses `math/big` rather than returning the wrapped value.

### PG-03 — Truthiness vs zero-value + comma-ok
**Why it bites:** Python `if x:` is false for `0`, `0.0`, `""`, `[]`, `{}`, `None`, `False`. A port to
`if x != nil` or `if x != ""` covers only one case; empty-but-non-nil collections and zero numbers flip
branches. `d.get(k)` returns falsy `None` on miss, while Go `v := m[k]` returns the zero value with no
signal — needs `v, ok := m[k]`.
**Detect:** `rg -n 'if not |if .*\.get\(|if [a-zA-Z_][a-zA-Z0-9_]*:'` (source); target `rg -n '\w+\[[^]]+\]'` map reads missing the comma-ok form; `ast-grep -l go -p '$V := $M[$K]'`.
**Test idea:** Pass an empty collection, a zero number, and a missing key; assert each branch matches Python's falsy outcome.

### PG-04 — Dict insertion order vs randomized map iteration
**Why it bites:** Python 3.7+ dicts preserve insertion order; Go `map` iteration order is randomized per
run. Any "first match", "pick one", or serialized-in-order output changes or becomes nondeterministic.
(`encoding/json` sorts map keys, so JSON masks this — custom range loops do not.)
**Detect:** `ast-grep -l go -p 'for $K, $V := range $M { $$$ }'` where the body appends to output or returns early; source loops over `dict`/`.items()` whose order feeds output.
**Test idea:** Run the path twice and assert identical, insertion-ordered output (or that the first-selected element is deterministic).

### PG-05 — Exception propagation vs dropped error return
**Why it bites:** Python exceptions propagate and crash loudly; Go errors must be checked, and `_ =`,
ignored multi-returns, or a forgotten `if err != nil` silently proceed with a zero value. A translated
`try/except` that becomes an unchecked call swallows the failure.
**Detect:** `rg -n '_,? *_? *(:?)= '` and `rg -n 'nolint:errcheck'`; run `errcheck ./...` / `golangci-lint` on the target; source `try:`/`except` blocks mapped to target call sites.
**Test idea:** Force the underlying op to fail and assert the error surfaces (non-nil return / non-2xx) instead of continuing with a zero value.

### PG-06 — `None` vs `nil` (typed-nil interface trap)
**Why it bites:** A `(*T)(nil)` stored in an interface (e.g. `error`) is `!= nil`. Returning a concrete
nil pointer as an interface makes `if err != nil` true on the success path. Python `None` has no such
trap. Also: nil-pointer deref panics where Python `None.attr` raises catchably.
**Detect:** `ast-grep -l go -p 'return $E'` in funcs whose declared return is `error`/an interface but `$E` is a concrete pointer type; `rg -n 'var \w+ \*'` returned into an interface.
**Test idea:** Exercise the success path and assert `err == nil` (guards against a typed-nil concrete error leaking as non-nil).

### PG-07 — JSON numbers → float64 precision loss
**Why it bites:** `encoding/json` decodes numbers into `interface{}`/`map[string]interface{}` as
`float64`; integers above 2^53 lose precision (IDs, nanosecond timestamps, big counters). Python `json`
keeps ints exact. Silent: the value is merely rounded.
**Detect:** `rg -n 'json.Unmarshal|json.NewDecoder'` decoding into `interface{}`/`map[string]interface{}`; `rg -n '\.\(float64\)'` on fields that are really int64.
**Test idea:** Round-trip an int64 > 2^53 (e.g. `9007199254740993`) through the decoder and assert the exact value — use `json.Number`/`Decoder.UseNumber()`.

### PG-08 — Mutable default arguments / shared collection state
**Why it bites:** Python `def f(x, acc=[])` shares the one default list across every call, accumulating
state between invocations. A faithful port that hoists the default to a package-level slice/map — or
that reslices a shared backing buffer — reproduces or introduces cross-call state leakage.
**Detect:** `rg -n 'def .*=(\[\]|\{\}|dict\(|list\()' ` (source); target package-level `var` slices/maps used as per-call defaults.
**Test idea:** Call the function twice; assert the second call does not observe the first call's mutations.

---

## Go version bump & Go → Go

Applies on a `go` directive / toolchain bump and to any Go-to-Go refactor that moves data across
ownership boundaries.

### GG-01 — nil-map write panic
**Why it bites:** Reading a nil map returns the zero value (fine); writing to one panics at runtime.
A zero-valued struct field of map type, or a map returned before `make`, blows up only on the write path.
**Detect:** `ast-grep -l go -p '$M[$K] = $V'` where `$M` may be a never-`make`d field; `rg -n 'map\[' ` struct fields; `rg -n 'var \w+ map\['`.
**Test idea:** Write to the map on a freshly zero-valued struct/return and assert no panic (map is initialized).

### GG-02 — append aliasing / shared backing array
**Why it bites:** `append` reuses the backing array when capacity allows. `append(s[:i], x)`, appending to
a sub-slice, or appending to a slice handed in by a caller can silently overwrite elements the caller
still holds. Corruption appears far from the append.
**Detect:** `ast-grep -l go -p 'append($S[$$$], $$$)'`; `rg -n 'append\([a-zA-Z_][\w.]*\[' `; audit funcs that append to a parameter slice.
**Test idea:** Append to a sub-slice, then assert the original slice's tail elements are unchanged (no aliased write-through).

### GG-03 — Pre-1.22 loop-variable capture
**Why it bites:** Before Go 1.22, `for _, v := range xs` reused ONE `v`; closures/goroutines capturing
`v` all saw the final value. Go 1.22 makes the loop variable per-iteration. A 1.21→1.22 bump changes the
behavior of any such capture — fixing latent bugs OR breaking code that relied on the shared variable.
**Detect:** `ast-grep -l go -p 'for $I, $V := range $XS { $$$ go func() { $$$ } $$$ }'`; `rg -n 'go func\(' ` and `rg -n 'append\(\w+, func'` inside range loops.
**Test idea:** Collect the closures/goroutines produced by a range loop and assert each observes its own iteration's value.

### GG-04 — `%w` wrap changing `errors.Is`/`errors.As`
**Why it bites:** Swapping `%v`↔`%w` in `fmt.Errorf` changes whether callers can `errors.Is`/`errors.As`
through the chain. Adding `%w` makes previously-opaque errors matchable (a `switch` may start catching
them); dropping it makes sentinel matches silently stop working.
**Detect:** `rg -n 'fmt.Errorf\('` (compare `%w` vs `%v`); `rg -n 'errors.Is\(|errors.As\('` for the match sites that depend on the chain.
**Test idea:** Assert `errors.Is(got, ErrSentinel)` (or `errors.As`) holds — or explicitly does not — across the change, at each matching site.

### GG-05 — `Truncate`/`Round` toward-zero vs floor for negatives
**Why it bites:** `time.Duration.Truncate`/`Round` operate on magnitude and truncate toward zero, not
toward −∞; negative durations round the "wrong" way versus a floor expectation. `time.Time.Truncate`
rounds down since the zero time and is UTC-relative, surprising for local-time bucketing.
**Detect:** `rg -n '\.Truncate\(|\.Round\('` on `time.Time`/`time.Duration` values; audit any that can be negative or that bucket local time.
**Test idea:** Truncate a negative duration (e.g. `-90m` to `1h`) and a pre-epoch time; assert the result matches the intended floor/UTC semantics, not toward-zero.
