# Migration Worthiness Memo — Template

Copy this skeleton and fill every section. Keep it to one page. Delete the
italic guidance lines. If a section can't be filled with evidence, that gap is
itself a finding — surface it, don't paper over it.

---

## Proposal

- **Unit:** _<what is being migrated — service / module / library>_
- **Source → Target:** _<current stack>_ → _<proposed stack>_
- **Stated motivation (verbatim):** _<the reason as originally given>_
- **Date / Author:** _<date>_ / _<who>_

## Bug-class table

*One row per structural bug class mined from the failure history (workflow step
2–4). Evidence = links to incidents / issues / PRs / commits. Frequency =
occurrences in the mining window. Severity = customer/on-call impact. Verdict =
STRONG (target eliminates at compile time / makes unrepresentable) or WEAK
(only marginal perf/taste/ecosystem). "Why" states the exact mechanism.*

| Bug class | Evidence | Freq | Severity | STRONG / WEAK | Why (compile-time mechanism, or why only marginal) |
|-----------|----------|------|----------|---------------|-----------------------------------------------------|
| _e.g. nil/null deref_ | #123, #145, INC-9 | 7/18mo | high | STRONG | _target's Option/Result makes an absent value unrepresentable; unwrap is explicit_ |
| _e.g. untyped-config drift_ | #201, INC-4 | 4/18mo | med | STRONG | _target parses config into a typed struct at startup; drift is a compile/parse error_ |
| _e.g. "raw speed"_ | (no bug evidence) | — | — | WEAK | _perf only; no bug class removed — address in-language_ |

*Summary line:* **N STRONG / M WEAK.** STRONG classes account for _<X%>_ of the
do-nothing cost below.

## Do-nothing cost

*What continuing on the current stack costs, tallied from the STRONG rows.*

- Bug rate: _<N bugs/quarter in these classes>_
- Incident / on-call toll: _<hours or pages / quarter>_
- Revert / hotfix rate, customer impact: _<…>_
- **Projected 2–3 yr cost:** _<rough total>_

## Effort budget

- Size: _<units / LOC (tokei/cloc)>_, _<# public entry points / endpoints>_
- Test surface to reach parity: _<count — hands to `test-census-parity`>_
- Rough AI translation + review budget: _<token / time / $ range>_
- **Budget vs do-nothing cost:** _<justified? by how much?>_

## Kill criteria

*Explicit, checkable conditions that ABANDON the migration mid-flight. If none
can be written, the answer is NO-GO.*

- [ ] _<e.g. differential golden harness can't reach parity after N units>_
- [ ] _<e.g. target needs unsafe/escape-hatch to express constraint C>_
- [ ] _<e.g. budget burns past 2× estimate at <30% of units complete>_
- [ ] _<e.g. a STRONG class turns out to need the same runtime discipline in target>_

## Recommendation

**GO / NO-GO / DEFER** — _<one line: which, and the single decisive reason>_

*Rationale (2–3 lines):* _<why the verdict follows from the table + cost +
budget + kill criteria>_

*Next step:*
- On **GO** → hand off to `migration-plan-and-discipline`.
- On **DEFER** → the in-language work that would change the verdict.
- On **NO-GO** → the WEAK motivations to address without a rewrite.
