# Normalization Checklist

Normalization removes non-determinism so the diff shows only meaningful differences. Two rules govern every entry below:

- **Symmetric.** Apply the exact same transform to OLD and NEW. Asymmetric normalization manufactures or hides diffs.
- **Justified.** Each rule erases a *known-volatile* field. If unsure whether a field is volatile or load-bearing, do NOT normalize it — leave it in the diff and triage it. Over-normalization is how a real regression sails through green.

Keep the raw captures; normalize copies. Prefer normalizing the *structured* form (parse JSON, then re-emit) over regex-on-text when the output has structure.

## Never normalize

- Exit codes and HTTP status codes — compare exactly.
- Error *classes* / messages that are part of the contract.
- Field presence vs absence, unless the contract truly treats `null` and missing as equal (decide once, apply both sides).
- Counts, totals, ordering that is semantically meaningful (e.g. a sorted result set the caller relies on).

## JSON / structured responses

- **Key order:** canonicalize. `jq -S .` (sorts object keys recursively) before diffing. Object key order is rarely part of the contract; array order usually is — do not sort arrays unless the producer's order is genuinely non-deterministic (see Ordering).
- **Volatile fields:** replace with a stable placeholder rather than delete (keeps shape diffs visible). Timestamps, `*_at`, durations/elapsed, request/trace/span IDs, generated UUIDs, hostnames, ports, PIDs, version strings, absolute paths.
  - `jq 'walk(if type=="object" then with_entries(if .key|test("_at$|^id$|^trace|^duration") then .value="<VOL>" else . end) else . end)'`
- **Floats:** round volatile floats to a fixed tolerance (`| .value|=(.*1e6|round/1e6)`), or compare with an epsilon. Watch integer-vs-float formatting (`1` vs `1.0`) and `-0` vs `0`.
- **Number/string formatting:** normalize scientific notation, trailing zeros, and quoted-number vs number if the two implementations differ cosmetically.
- **Unicode:** apply the same NFC normalization and the same escaping policy (`é` vs literal `é`) to both.
- **Empty containers:** decide `[]`/`{}` vs missing once, apply both sides.

## CLI / plain text

- **ANSI escapes / color:** strip. Set `NO_COLOR=1`/`TERM=dumb` at capture time; belt-and-suspenders strip: `sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g'`.
- **Line endings:** CRLF → LF (`tr -d '\r'`). Strip trailing whitespace per line; normalize a trailing final newline.
- **Timestamps:** mask ISO-8601 and clock strings — `sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9:.,]+(Z|[+-][0-9:]+)?/<TS>/g'`.
- **Absolute & temp paths:** collapse to a placeholder — build dirs, `$HOME`, `/tmp/xxxx`, worktree paths, CWD. `sed -E "s#$PWD#<CWD>#g; s#/tmp/[A-Za-z0-9._-]+#<TMP>#g"`.
- **Volatile tokens:** UUIDs (`s/[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}/<UUID>/g`), hex addresses (`0x[0-9a-f]+`), PIDs, ports, durations (`\d+(\.\d+)?(ns|µs|ms|s)`), byte sizes, progress bars/spinners/percentages.
- **Tables / alignment:** column padding differs harmlessly — squeeze runs of spaces (`sed -E 's/ +/ /g'`) only if alignment is not part of the contract.
- **Locale:** pin `LC_ALL=C` so number/date/sort formatting is stable.

## Logs

Logs are the noisiest surface; normalize aggressively but keep the message body and level.

- Mask timestamps, log-level padding, trace/span/request IDs, goroutine/thread IDs, memory addresses, hostnames, PIDs.
- **Stack traces / file:line:** mask line numbers and absolute source paths if they drift with unrelated edits, but keep symbol/function names.
- **Ordering:** interleaved concurrent log lines are non-deterministic — either capture single-threaded, or `sort` the normalized lines before diffing (last resort; it hides ordering regressions).
- **Startup banners / build metadata / version lines:** drop known-volatile whole lines with a grep filter.

## Ordering & concurrency

When output order is a genuine non-deterministic artifact (map/set iteration, concurrent workers, unstable sort), impose a deterministic order before diffing:

- JSON arrays that are logically sets: sort by a stable key.
- Text lists: `sort` after per-line normalization.
- Prefer fixing the *producer* to emit a stable order (seed maps, sort output) over sorting in the normalizer — a stable producer is testable; a sorting normalizer masks real reordering regressions. Note any sort applied here as reduced coverage.
