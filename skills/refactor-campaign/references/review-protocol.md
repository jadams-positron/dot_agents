# Review protocol

Use these schemas verbatim so independent reports can be combined without
losing evidence.

## Coverage ledger

Record one row per tracked path or coherent generated/vendor group:

| Path or group | Kind | In scope | Reviewer | Result | Exclusion reason |
|---|---|---:|---|---|---|

Generate the inventory from the repository rather than memory. Supplement the
tracked-file list with language-native package/module discovery. Treat tests as
first-class code. Include build, release, migration, and operational code when
it can reveal responsibility or dependency problems relevant to the goal.

## Pass 1 reviewer prompt

Provide the frozen goal, repository instructions, assigned paths, and baseline
SHA. Ask the reviewer to inspect every assigned path and return only the
following records plus a coverage confirmation:

```text
Finding ID:
Evidence: file:line and current control/data flow
Cost: concrete complexity, duplication, coupling, or maintenance consequence
Goal relevance:
Proposed unit:
Behavior and safety invariants:
Tests that would prove preservation:
Likely files:
Dependencies or overlap:
Confidence:
```

Forbid edits, implementation, generic style advice, and conclusions based only
on names or file size.

## Pass 2 lens prompts

Give fresh reviewers the frozen goal, baseline SHA, full repository, and one
lens. Do not provide pass 1 reports. Require them to trace call sites and tests
before proposing a boundary change.

For abstraction proposals, require a concrete repeated contract and a rough
before/after complexity argument. For safety or concurrency code, require the
specific invariant and adversarial scenario that must remain covered. For
package moves, require evidence that dependency direction and cohesion improve
without creating an import cycle or dumping ground.

Use the same finding schema as pass 1.

## Pass 3 validator prompt

Provide the frozen goal, repository instructions, baseline SHA, and a batch of
raw findings. Do not provide coordinator judgments. Require one verdict per
finding:

```text
Finding ID:
Verdict: real | duplicate | unsupported | out-of-scope | behavior-risk
Verified evidence:
Value and goal relevance:
Duplicate or conflict IDs:
Smallest cohesive work unit:
Behavior and safety boundary:
Required tests:
Files and dependency edges:
```

Require the validator to inspect the current code and reject plausible prose
that lacks code evidence.

## Work-unit manifest

Assign stable IDs after deduplication:

```text
Unit ID and slug:
Source finding IDs:
Outcome:
Why it is high value:
Owned files or symbols:
Permitted supporting files:
Explicit non-goals:
Behavior and safety invariants:
Required red test or characterization:
Focused verification:
Full-gate impact:
Prerequisite unit IDs:
Expected conflicts:
Starting SHA:
Status:
```

Keep rejected and combined findings beside the accepted manifest. A campaign
is not comprehensive when inconvenient observations simply disappear.
