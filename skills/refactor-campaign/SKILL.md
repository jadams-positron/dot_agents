---
name: refactor-campaign
description: Run an auditable three-pass, multi-agent review of an entire codebase against a broad refactoring or code-organization goal, validate and deduplicate the findings into dependency-ordered work units, implement each accepted unit in an isolated git worktree, integrate the resulting local commits serially into the current feature branch, and independently review the final diff for abstraction alignment in a clean context. Use when the user asks for a comprehensive codebase refactor campaign, wants every package reviewed for maintainability opportunities, or requests fan-out implementation of validated improvements with local integration. Do not use for a routine single-fix review or issue-per-PR fan-out.
---

# Refactor Campaign

Review the whole requested code surface, turn evidence-backed findings into a
bounded work graph, and integrate independently audited worker commits into the
current branch. Keep remote delivery outside this skill; when paired with
`work-issue`, return the clean integrated branch to that workflow before it
pushes or opens a PR.

## Authorization and ownership

Treat explicit invocation in execute mode as approval to create local branches
and sibling worktrees, let workers edit and commit only there, merge those
campaign branches into the current integration branch, and remove only
campaign-created worktrees and fully merged local branches after verification.
Do not push, open or merge a PR, rewrite pre-existing history, delete unrelated
work, or modify an unrelated checkout.

Keep the invoking session as coordinator and sole writer to the integration
worktree. Keep all implementation in worker worktrees. Never let reviewers or
workers spawn their own subagents. Tell every agent that other agents share the
repository and that it must not revert, clean, or overwrite their work.

## Select the mode and bound

Use `review-only` when the user asks only for findings or a plan. Use `execute`
when the user asks to implement or integrate the improvements. In execute mode,
accept a user-supplied maximum unit count; otherwise use eight. Complete all
three review passes even when the accepted set exceeds the implementation
bound, then stop after the manifest and ask before exceeding it. Do not lower
the evidence or value threshold merely to fill the bound.

Require at least two independent reviewer agents in every pass. Use up to three
concurrent agents when the host allows it, leaving the coordinator slot free.
If fan-out is unavailable, stop instead of quietly replacing independent review
with self-review.

## Freeze the campaign

1. Read the repository instructions and the issue, plan, or goal that defines
   relevance. Restate the scope, behavior constraints, and acceptance gates.
2. Resolve the intended integration branch and its base. Reuse an
   orchestrator-created worktree and branch exactly. Do not rename it or create
   a second integration worktree.
3. Require a clean integration worktree. Preserve unrelated state and stop if
   existing edits make the baseline ambiguous.
4. Bring the branch current only through an already-authorized outer workflow.
   Otherwise ask before rewriting it. Record the integration branch, base ref,
   full base-tip and base-to-baseline merge-base OIDs, baseline commit, baseline
   tree, and full gate command.
5. Run the full gate on the untouched baseline. Stop on an unexplained baseline
   failure; do not let campaign changes hide it.
6. Create a durable campaign state file below
   `<git-common-dir>/codex-campaigns/<campaign-id>.md`. Record the frozen scope,
   coverage ledger, raw findings, dispositions, unit DAG, worktree paths,
   commits, tests, integration SHAs, and repeated-failure counts. Update it at
   every phase boundary and before context compaction.

After compaction, reread this skill, repository instructions, and the complete
state file; then verify the current branch, worktrees, and recorded SHAs before
continuing.

## Run the three review passes

Read [review-protocol.md](references/review-protocol.md) in full before
dispatching reviewers.

### Pass 1: coverage census

Mechanically inventory all tracked source, tests, commands, and relevant build
or operational code. Mark generated, vendored, fixture, and irrelevant paths
explicitly rather than silently omitting them. Partition every in-scope path
among non-overlapping reviewer shards. Give each reviewer the frozen goal and
its paths, but no proposed findings.

Do not close the pass until every inventory row has a reviewer result or a
written exclusion reason.

### Pass 2: independent cross-cutting lenses

Use fresh agents that do not see pass 1 findings. Assign repository-wide lenses
covering at least:

- control flow, cohesion, branch-heavy functions, and unclear responsibilities;
- duplication, concrete repeated contracts, dependency direction, and package
  boundaries;
- error handling, concurrency, safety invariants, testability, and behavioral
  preservation.

Require file-and-line evidence. Reject style preferences without a concrete
maintenance, correctness, or complexity cost.

### Pass 3: adversarial validation

Combine raw pass 1 and pass 2 findings without coordinator verdicts and
distribute them in batches to fresh validators. Require validators to inspect
the code, challenge relevance and value, identify duplicates and conflicts,
and name the behavior boundary and tests for each real finding. Assign a
separate coverage check to confirm that the ledger has no silent gaps.

### Pass 4: independent abstraction alignment

Before synthesis in both review-only and execute modes, dispatch
`abstraction-review` in a brand-new read-only agent with no inherited campaign,
authoring, or reviewer context. This pass occurs before campaign implementation,
so never describe its target as a baseline-to-current diff when those commits
are identical.

Freeze one of these two real targets:

- If the campaign branch already differs from its integration base, give the
  reviewer the full base-tip, merge-base, and baseline OIDs plus the exact
  merge-base-to-baseline binary diff and SHA-256.
- If there is no pre-existing branch diff, run a goal-scoped repository
  abstraction census instead. Give the reviewer the exact baseline commit and
  tree OIDs plus a complete in-scope tracked-path/blob-OID census and its
  SHA-256. Ask it to use the skill's null-diff and owner-mapping method to find
  existing parallel mechanisms, identity dispatch, runtime rediscovery, guard
  workarounds, and contract shoehorning relevant to the raw refactor goal. Do
  not manufacture or review an empty diff.

Require a clean worktree and give it only that frozen target, the frozen goal
and acceptance boundaries, and repository instructions. Do not pass raw
findings, validator output, a draft manifest, proposed units, suspected
problems, or fixes. In Codex use `fork_turns: "none"`;
in another harness use its equivalent fresh-context task. Tell it to load and
follow the installed `abstraction-review` skill and references and inspect the
shared path and history itself. Re-resolve every recorded OID, the artifact
digest, HEAD/tree, and worktree cleanliness after collection; discard and
restart on any mismatch. Add every
returned finding to the raw ledger so synthesis gives it an explicit
disposition. Enforce a positive tool allowlist containing only file read/search
and exact non-mutating history/diff commands; explicitly deny
Write/Edit/NotebookEdit, mutation-capable shell, and state-changing MCP/external
tools. Post-hoc cleanliness is not enforcement. If isolation or allowlist
enforcement is unavailable, stop.

## Synthesize the work manifest

Give every raw finding exactly one disposition: `accepted`, `combined into
<id>`, or `rejected` with a code-grounded reason. Accept a unit only when it:

- directly advances the frozen goal and has concrete evidence;
- produces a meaningful reduction in complexity or responsibility ambiguity;
- preserves behavior and safety unless a behavior change was explicitly
  authorized;
- has a bounded implementation, clear ownership, and a proving test plan;
- avoids speculative interfaces, generics, helpers, or package churn; and
- does not overlap another accepted unit unless ordered by a dependency edge.

Cluster overlapping findings into one unit. Build a DAG from API, schema,
generated-artifact, file-overlap, and semantic dependencies. Freeze the
manifest before implementation. Do not silently add later discoveries; record
and validate them through the same disposition process.

In review-only mode, report the manifest and stop. In execute mode, stop for
approval when the accepted unit count exceeds the configured bound; otherwise
continue without another gate.

## Execute ready units in isolated worktrees

Read [worker-integration.md](references/worker-integration.md) in full before
creating worktrees or dispatching workers.

Schedule only DAG-ready units, in waves of at most three. Create sibling
worktrees outside the integration worktree. Use branch names such as
`refactor-<campaign>-u01-<slug>`; never append a child path beneath the existing
integration branch name because Git refs can collide. Create each root unit
from the frozen baseline and each dependent unit only after its prerequisites
are integrated, using the recorded integration SHA.

Give one worker sole responsibility for each unit and its worktree. Require it
to read repository instructions, follow TDD when required, stay within the
manifest, run focused tests, keep the worktree clean, create signed commits when
the repository requires them, and report the commit SHA plus exact verification
output. Forbid pushes, PRs, merges, rebases, worktree cleanup, hook bypasses, and
unapproved scope expansion.

Serialize commit and pre-commit gates when sibling worktrees share linter,
compiler, or cache locks. Never kill a sibling process or bypass a hook to make
a commit succeed.

After a worker commits, dispatch a fresh read-only audit agent with the frozen
unit, its diff, and verification claims. Require a `fess`-style evidence audit.
Enforce a positive tool allowlist limited to file read/search and exact
non-mutating history/diff commands; deny write tools, mutation-capable shell,
and state-changing MCP/external tools. If enforcement is unavailable, stop
instead of calling the audit read-only.
Validate its findings, send real ones back to the original worker, and require
the worker to amend and reverify before integration. Stop after three repeats of
the same failing signature without progress.

## Integrate serially

Keep the integration worktree clean and integrate exactly one audited unit at a
time. Verify the unit branch, declared base, commit signature when required,
diff scope, and test evidence. Prefer a local non-fast-forward merge so unit
provenance remains visible until the outer workflow performs final history
cleanup; honor a repository's stricter linear-history rule when present. Never
bypass required signing.

If a merge conflicts, abort it without touching unrelated work and return the
unit to its worker against the latest recorded integration SHA. Do not guess at
cross-unit intent in the integration worktree.

Run the unit's focused tests after every merge and the project full gate after
every wave. Route a regression back to the responsible worker and re-audit the
repair. Record the merge SHA and evidence before scheduling dependents.

## Final campaign gates

1. Reconcile the frozen manifest: every accepted unit must be integrated and
   every raw finding must retain a disposition.
2. Run the complete project gate on the integrated tree.
3. Use `test-census-parity` when the campaign claims behavior preservation.
   Use `differential-golden-harness` as well when an old/new CLI, handler, or
   pure-transform output can be compared meaningfully.
4. Dispatch a fresh final auditor over the complete baseline-to-HEAD diff and
   all test claims. Turn each validated final finding into a new bounded worker
   unit rather than fixing it directly in the integration worktree. Count final
   repair units against the same configured implementation bound.
5. Independently dispatch `abstraction-review` over the complete
   baseline-to-HEAD diff. Use a brand-new read-only agent with no inherited
   conversation, campaign, worker, or reviewer context. Give it only the frozen
   goal and acceptance boundaries, repository/worktree and instructions, full
   40-hex baseline and head commit OIDs, and the exact diff artifact plus
   SHA-256. Tell it
   to load and follow the installed `abstraction-review` skill and required
   references, inspect the shared path and relevant history itself, and return
   the complete verdict and evidence-backed findings. Require a clean worktree.
   Do not pass the campaign
   manifest, raw findings, implementation plans, prior audits, proposed fixes,
   or suspected problems. In Codex use `fork_turns: "none"`; in another harness
   use its equivalent fresh-context task. A general final auditor does not
   satisfy this leg. Re-resolve both OIDs and the digest and recheck worktree
   cleanliness after collection; discard and restart the review on any mismatch.
   Apply the same positive read-only tool allowlist as Pass 4; if isolated
   dispatch or allowlist enforcement is unavailable, stop.
6. Turn each validated abstraction finding into a bounded worker unit under the
   same repair and implementation-bound rules. After any repair, rerun affected
   gates and use a different fresh abstraction reviewer against the new exact
   head. An unverified premise that needs an owner's answer blocks integration.
7. Repeat the affected gates until both final audits are clean, with the same
   three-attempt escalation bound.
8. Verify every campaign commit is reachable from the integration branch and
   the worktree paths match the state file. Remove only clean,
   campaign-created worktrees without force, then delete only fully merged
   campaign branches. Leave any uncertain artifact intact and report it.

When composed with `work-issue`, return control before any push and let that
skill perform its gate chain, tree-preserving history cleanup, PR, CI, and
Bugbot workflow. Report the integrated branch and SHA, accepted/rejected counts,
unit commits and merge SHAs, test evidence, cleanup result, and open decisions.
Include the abstraction reviewer's identity, context-isolation method, reviewed
baseline/head, verdict, and disposition of every finding.

## Escalate

Stop when requirements or a dependency edge require guessing, the baseline is
not reproducible, a requested unit would cross repositories without authority,
an agent produces unusable work twice, the same gate fails three times without
progress, a conflict cannot be resolved from the frozen intent, or an action
would modify or delete anything outside campaign ownership.
