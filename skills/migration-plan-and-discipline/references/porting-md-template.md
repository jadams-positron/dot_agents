# PORTING.md — Translation Guide

Copy this file to `PORTING.md` at the migration root. It is the single source of
truth for how every source idiom becomes a target idiom. Every executor (human or
`fix-all` subagent) follows it; deviations are review blockers, not judgment calls.

Rule of the guide: **one row per recurring idiom, exactly ONE worked before/after
example per row.** More than one example per row means the row is really two rows.
No example means the row is not yet real — leave it as a `TODO` and it blocks
`gate-translated`.

## How to mine the idioms (do this first, don't guess)

Discover what actually recurs in the source before writing rows:

```bash
# Count constructs so the guide covers the frequent ones, not the imagined ones.
rg -c 'except |raise |with |yield |async def |@dataclass' -g '*.py' | sort -t: -k2 -rn
# Structural search for a specific idiom (any language pair):
ast-grep --lang python -p 'with $CTX as $V: $$$'      # resource cleanup
ast-grep --lang python -p 'def $F($$$) -> Optional[$T]: $$$'   # nullable returns
```

Rank rows by frequency. The top ~15 idioms usually cover >90% of the port.

## Idiom mapping table

| # | Source idiom | Target idiom | Rule / notes | Worked example (before → after) |
|---|--------------|--------------|--------------|----------------------------------|
| 1 | _e.g. `Optional[T]` return_ | _e.g. `(T, bool)` or `*T`_ | Pick ONE per the decisions ledger's nil-vs-zero policy; do not mix. | `def find(id) -> Optional[User]` → `func Find(id string) (*User, bool)` |
| 2 | _resource cleanup (`with`)_ | _`defer`/RAII/`try-finally`_ | Ownership per ledger: the opener closes. | `with open(p) as f: ...` → `f, err := os.Open(p); defer f.Close()` |
| 3 | _exceptions_ | _returned errors / Result_ | Wrap per ledger error-wrapping convention; never swallow. | `raise NotFound(id)` → `return fmt.Errorf("find %s: %w", id, ErrNotFound)` |
| 4 | _iteration/comprehension_ | _explicit loop / iterator_ | Preserve order and short-circuit semantics. | `[f(x) for x in xs if p(x)]` → `for _, x := range xs { if p(x) { out = append(out, f(x)) } }` |
| 5 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |

Add rows until the mined idiom list is exhausted. Keep the numbering stable — the
decisions ledger and review comments reference rows by number.

## What this port does NOT change (banned — deferred to labeled follow-up)

Structure-preserving translation only. The following are **forbidden inside the
port** and captured as a separate, labeled follow-up (`cleanup/idiomatic-*`) run
only after cutover:

- Renaming symbols, files, or packages away from their source names.
- Reordering declarations within a file, or splitting/merging files.
- Deduping repeated code, extracting helpers, or re-layering abstractions.
- Reducing `unsafe`/`any`/`interface{}`/reflection introduced to mirror source shape.
- Performance rewrites, added concurrency, or API "improvements".

Each is legitimate later — but landing it during the port destroys diffability and
`git bisect`. If an executor believes a cleanup is unavoidable, it goes in the
follow-up backlog, not the port.
