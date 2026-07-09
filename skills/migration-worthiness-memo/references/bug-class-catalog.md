# Bug-Class Catalog & STRONG/WEAK Heuristic

Use this to bucket mined failures (workflow step 3) into structural *classes* and
to classify each against the proposed target (step 4).

## The core test: STRONG vs WEAK

A bug class is **STRONG** for a target only if the target **eliminates it at
compile time or makes the buggy state unrepresentable by construction** — such
that a developer (or an AI porting the code) *cannot* reintroduce it without
loud, local, mechanical failure (compile error, exhaustiveness error, borrow
error, parse-at-startup error).

A class is **WEAK** if the target only makes the bug *less likely, faster to hit,
or nicer to write* — it still compiles. WEAK motivations (perf, idiom/taste,
library ecosystem, async model preference, hiring/familiarity) **do not justify a
rewrite**; address them in-language or defer.

Litmus questions for STRONG:
- Can the old bug even be *written* in the target? If it won't compile → STRONG.
- Is the check mechanical and total (every call site, at build time), or does it
  rely on runtime discipline / lint / convention / reviewer vigilance? Only the
  former is STRONG.
- Does the guarantee survive an AI translating code mechanically? A guarantee
  that a careful human upholds but the compiler doesn't is WEAK.

Beware **false STRONG**: a target feature that *permits* safety but has an escape
hatch the port will lean on (e.g. `unsafe`, `any`/`interface{}`, `unwrap()`
everywhere, `# type: ignore`, reflection) is only as strong as the discipline
enforcing the escape hatch stays unused. Note the escape hatch in the "Why"
column.

## Common structural bug classes

Bucket the mined incidents/issues/commits into classes like these. The class is
about what the *source stack allows by construction*, independent of any one bug.

- **Manual-lifetime memory errors** — use-after-free, double-free, buffer
  overrun, leak from manual alloc/free.
- **Data races on shared mutable state** — unsynchronized access across threads.
- **Null / nil dereference** — an absent value flowing where a present one was
  assumed.
- **Untyped / schema-drift config & data** — config, env, JSON, or DB rows read
  as loose maps/dicts; a renamed/missing field explodes at runtime far from the
  edit.
- **Stringly-typed errors / control flow** — errors as strings/codes compared by
  text; error cases silently unhandled.
- **Non-exhaustive case handling** — a new enum/variant/state added, some
  switch/match not updated.
- **Unchecked exceptions / silent failure** — a call that can fail whose failure
  path is never handled.
- **Implicit type coercion / numeric issues** — silent narrowing, overflow,
  float/int confusion, bytes-vs-text.
- **Unit / dimension / ID mix-ups** — passing the wrong-but-same-underlying-type
  value (seconds vs ms, userID vs orgID).
- **Resource-cleanup ordering** — files/sockets/locks/transactions not released
  on every path.

## Worked source→target mappings

These are language-pair-general (apply to any repo using the pair). Verify
against the *actual* target feature set and how the port will be written.

| Bug class | STRONG in target(s) | WEAK / caveat |
|-----------|---------------------|----------------|
| Manual-lifetime memory errors | Rust (ownership/borrow), any GC'd language (Go, Java, C#) | STRONG only if the port drops raw pointers; Rust `unsafe` blocks reopen it |
| Data races | Rust (`Send`/`Sync` + borrow check) | Go **WEAK** — race detector is runtime/opt-in, not a compile guarantee |
| Null / nil deref | Rust (`Option`), Kotlin/Swift null-safety, TS `strictNullChecks` | Go **WEAK** — nil pointers/interfaces still compile; not eliminated |
| Untyped config / schema drift | Any statically-typed target that parses config into typed structs at startup (Go, Rust, TS) | STRONG only if parsing is total & at boundary; leaving `map[string]any`/`any` keeps it WEAK |
| Stringly-typed errors | Rust (`Result` + typed enums), Go (typed error values + `errors.Is/As`) | Go partial — errors can still be ignored (`_ =`); linters help but aren't the compiler |
| Non-exhaustive case handling | Rust (`match` exhaustiveness), TS (discriminated unions + `never`), Swift | Go **WEAK** — `switch` needs no default; not enforced |
| Unchecked exceptions / silent failure | Go (explicit `error` returns), Rust (`Result`, `#[must_use]`) | Checked-exception languages help; but only STRONG if the value is must-use |
| Implicit coercion / numeric | Rust (explicit casts, checked/overflowing ops), typed langs vs dynamic | Overflow WEAK unless target checks it (Rust debug/`checked_*`); C/Go wrap silently |
| Bytes-vs-text confusion | Py2→Py3, or any target with distinct `str`/`bytes` | WEAK if both map to one type |
| Unit / ID mix-ups | Targets with cheap newtypes/`type`-distinct wrappers (Rust, Go named types, TS branded types) | STRONG only if the port actually introduces the newtypes — same underlying type stays WEAK |

## Pure-WEAK motivations (never sufficient alone)

Flag these in the memo as reasons to DEFER/NO-GO unless they map to a STRONG
class above:

- "It'll be faster." → benchmark & optimize in-language first (`investigate-performance`).
- "It's more idiomatic / cleaner / modern."
- "Better library / framework ecosystem for Z."
- "The team prefers / knows the target better."
- "Different concurrency/async model." (unless it removes the data-race class)

If the top rows of the bug-class table are all WEAK, the recommendation is
NO-GO or DEFER — the current stack isn't *structurally* the problem.
