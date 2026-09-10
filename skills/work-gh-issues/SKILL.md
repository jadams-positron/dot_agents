---
name: work-gh-issues
description: Use when asked to discover, batch, launch, or work GitHub issues through Agent Deck, including independent issues and native pull-request stacks.
---

# Work GitHub Issues

Load `change-control`, its feedback-disposition reference, and [the consume-only upstream caller contract](../change-control/references/upstream-skills.md). Superpowers stays unchanged; the owned workflow supplies execution/admission precedence. Use [the owner-state protocol](references/owner-state.md) for launch, repair, feedback, and terminal checkpoints. Roll out this revision only with its matching launcher/state helper, review schema v4 consumers, and verified goal-terminal support; do not auto-adopt legacy active sessions.

Deliver the smallest complete, verified feature. Treat review feedback as evidence to adjudicate, not a list of changes to accept. Finish when the original feature criteria and required current-candidate evidence pass—not when reviewers have exhausted all suggestions.

## Ownership and authorization

Use Agent Deck for durable sessions and worktrees. Use Pi subagents for bounded planning, review, and investigation; never substitute temporary subagent worktrees for issue/stack owners.

Separate the dispatcher from implementation owners:

- The dispatcher selects repositories/issues, plans dependencies, launches owners, records their identities, and reports outcomes. It never repairs or pushes an owner's branches.
- A singleton runs `work-issue` in standalone mode as its sole root.
- One stack owner runs this contract for its entire chain. Each `work-issue` member is a delegated leaf: implement, run focused checks, leave the authorized local commit, and return.
- Each root alone owns its scope, finding ledger, counters, agents, commits, pushes, CI, and completion. Reviewers and other leaves do not dispatch, repair, restart reviews, or reset budgets.

Invocation authorizes the selected feature's implementation, proving tests, necessary corrections within the authorized repositories, normal issue-branch commits/pushes, draft PRs, supported issue/project hygiene, justified review-thread dispositions, and review-ready state. It also authorizes useful deduplicated follow-up issues through the repository's `issue-templates` and `file-issue` conventions. Do not manufacture metadata, tickets for trivial preferences, or unrelated feature work.

Preserve explicit user restrictions, repository safety rules, credential boundaries, worktree-script trust, and ownership of shared history. Never merge, release, deploy, change production pins/protection settings, delete user work, or silently expand the requested product behavior. An estimated file list or LoC forecast is not an explicit prohibition.

## 1. Select the repository

Accept a GitHub URL, `OWNER/REPO`, or local checkout path. If absent, run:

```bash
python3 <skill-dir>/scripts/discover.py repos --profile <profile> --limit 5 --json
```

Offer the five recent repositories with paths and last-activity times, accept a number/slug/URL/path, and wait for that genuine selection. Do not choose for the human. Continue the same invocation after the answer.

Resolve the selection and discover issues:

```bash
python3 <skill-dir>/scripts/discover.py resolve <selection> --profile <profile> --json
python3 <skill-dir>/scripts/discover.py issues OWNER/REPO --profile <profile> --json
```

Require a real worktree on the repository's default branch as the launch base. A bare repository or feature-only worktree set is not sufficient. If discovery returns no `local_path`, request a default-branch checkout; do not clone or create one without authorization.

## 2. Select actionable issues

Accept positive issue numbers as `21`, `#21`, or comma/whitespace-separated lists. Without numbers, show discovery's categories and reasons:

- `available`: open, unblocked, unassigned, and without an active issue session/worktree/branch/PR;
- `in_progress`: already claimed;
- `blocked`: open dependencies or blocked/on-hold labels.

Select the whole available set only when explicitly requested; otherwise ask which numbers or `all`. If none are available, report that and launch nothing. Never silently include claimed or blocked issues.

## 3. Build dependency chains

Inspect each selected issue's full title, body, comments, and native `blockedBy`/`blocking` relations:

```bash
python3 <skill-dir>/scripts/discover.py inspect OWNER/REPO <issue> [<issue> ...] --json
```

Inspect enough source to find existing owners and likely shared write surfaces. Derive dependencies from evidence:

- Add hard edges for explicit prerequisites or required API/schema/artifact production.
- Add ordering edges for predictable foundational overlap with a defensible implementation order.
- Leave unrelated work independent; a shared label/subsystem alone does not require a stack.
- Include an unselected prerequisite only with the appropriate selection authorization; otherwise omit the dependent and report it.
- Treat changelogs, lockfiles, generated artifacts, migrations, and release metadata as write-set hotspots. Assign one owner or serialize genuinely conflicting changes.

Build reviewable topological chains; preserve true prerequisites. Detect cycles, multiple immediate parents, or ambiguous branching rather than inventing an order. Native PRs have one immediate base. If intent is genuinely ambiguous, request that decision—not an implementation allowance for every new file.

Launch one owner/worktree for each independent issue or entire chain. Worktrees isolate files, not remote refs or stack history. Never launch concurrent writers for members of the same native `gh stack`.

## 4. Launch and persist identities

Use the bundled launcher; do not reconstruct `agent-deck launch` commands:

```bash
python3 <skill-dir>/scripts/launch.py \
  --repo <default-branch-checkout> <issue> [<issue> ...] \
  --profile <profile> --batch-file <durable-batch-manifest> \
  [--parent <session-id>] [--group <group>] [--name-prefix <prefix>] \
  [--instructions-file <path>] [--depends-on <child>:<immediate-parent> ...] --json
```

`--depends-on 22:21 --depends-on 23:22` describes one owner for a three-member stack. Resume with `--repo <same-checkout> --profile <same-profile> --batch-file <same-path> --resume --json`; do not repeat issues/dependencies or create a fresh batch to bypass collision checks.

Defaults remain:

- repository directory name as the Agent Deck group;
- `work#<root-issue>` as requested title/branch handle;
- the existing subdirectory worktree location, with actual paths normalized by Agent Deck;
- native Pi with its configured default model and `--no-approve`; its wrapper carries the durable owner identity and state paths;
- current Agent Deck parent linkage and the completion-sentinel request.

Use explicit user overrides for group/prefix. Scope every lookup to the profile. Do not add `--no-parent`. Treat actual session IDs, normalized branch/worktree paths, parent, and default base returned by Agent Deck as authoritative. Derive child branches from the actual prefixed root branch.

Append user-specific constraints with `--instructions-file`; never include secrets. The launcher's stored owner prompt must reference this contract and the exact owner-state path rather than duplicate the whole process.

Before creation, revalidate open/claimed state, dependency order, checkout, collisions, and script trust. Accept a blocked member only when every open blocker is selected and ordered below it. De-duplicate issue numbers; lock titles; record and continue past an independent launch failure.

Inspect repository-owned `.agent-deck/worktree-*.sh` scripts and obtain explicit approval of their current content with `agent-deck worktree trust-scripts <repo-path>`. Never grant trust implicitly.

Keep the batch file outside repository worktrees. The launcher persists intent and registers reservations for every selected stack member before creating anything, then persists each actual owner identity immediately afterward. Discovery includes those durable reservations across profiles; titles are not chain-membership records. On a lost response, reconcile registry/GitHub evidence before retrying. Adopt only a provable matching owner; ambiguous identity is a safe stop, not permission to launch another writer.

## 5. Freeze the feature contract and plan through existing abstractions

Each owner records raw issue criteria, derived acceptance checks, non-goals, safety invariants, authorized repositories/operations, base, risk, expected files and gross handwritten diff, generated artifacts, and required gates. Keep estimates distinct from explicit prohibitions. A necessary in-feature shared-path correction may update an estimate without human approval.

Before implementing each feature, dispatch one clean-context read-only planning agent. Require it to load `abstraction-review` and:

1. Locate the existing abstraction that owns the responsibility.
2. Inspect its extension points, nearest analogous implementation, relevant history, and tests.
3. State the null-diff shape: what would change if the existing design already fit?
4. Ask: **“Can this feature be implemented in less than 100 lines?”**
5. Identify the smallest complete shared-path change, its proving tests, and any doubt about unnecessary machinery.

Provide raw criteria, repository instructions, and source—not an authoring transcript or a defended solution. This planning use of the skill does not satisfy the final canonical independent-review gate.

If the planner expresses doubt, dispatch one additional fresh-context agent:

> **There MUST be a better way! Find a smaller complete implementation through the existing abstractions, or their smallest necessary extension. Preserve every acceptance criterion and safety invariant.**

Compare concrete alternatives and choose the smallest correct, clear approach. The second search may find no defensibly simpler solution. Do not repeat the challenge after ordinary patches or force a 99-line answer. Record production, test, documentation, and generated churn separately; never weaken tests, obscure code, or move complexity elsewhere to satisfy a count.

## 6. Implement with the local test loop

Use the approved feature contract and repository TDD conventions:

```text
implement → focused tests → diagnose/correct → focused tests
```

Do not launch review/adjudication agents for each edit or ordinary test failure. Diagnose necessary corrections locally, preserve a useful reproducer, and account for changed surface. Record optional discoveries without implementing them. Investigate uncertainty with available evidence before treating it as a missing human decision.

Respect explicit restrictions and genuine product/authority boundaries. Never hide a newly introduced correctness or security defect behind “outside the estimated files.” Never broaden the feature merely because a reviewer suggests a more general framework.

A singleton follows `work-issue` under this shared policy. A stack owner initializes `gh stack init --base <default> <actual-root-branch>`, then processes members bottom-to-tip using `gh stack add <derived-child-branch>`. Delegated members perform their bounded implementation and focused checks; only the owner dispatches planning/review agents or publishes. Preserve each member's coherent signed commit when required and its own user-visible changelog entry.

## 7. Review one stable candidate and adjudicate claims

Run the risk-appropriate stable-candidate review. For stacks, run one aggregate review of composition rather than a broad review for every member plus another aggregate review. Members still require their own acceptance and focused checks.

Put adjudication in the existing local-review verification stage; do not append another panel afterward. Use one independent read-only adjudicator per coherent batch by default. Partition oversized batches only as needed and account for every claim. Do not create two agents per individual comment, demand finding quotas, or promote a finding because several reviewers agree.

Give the adjudicator the raw feature criteria, exact candidate, relevant source, raw claims, and supported prior dispositions. Require answers to:

- **Is this issue critical to the feature being implemented? Which criterion or invariant does it affect?**
- **Will the feature be incomplete without this recommendation?**
- **Is the reported issue valid and defensible? What evidence supports or refutes it?**
- **Is the issue valid but outside this feature's scope? If so, is a deduplicated follow-up issue worthwhile?**
- **What is the smallest complete correction—not necessarily the reviewer's proposed correction?**

Record factual validity separately from necessity and severity. Use the shared `change-control` disposition contract:

| Disposition | Required response |
|---|---|
| `required_now` | Fix a defensible acceptance failure, introduced regression, safety violation, or genuine required-gate failure. |
| `follow_up` | Preserve a valid concern that is not necessary for this feature; track it separately when useful. |
| `no_change` | Explain the evidence for intended behavior, an already handled/duplicate claim, a disproved concern, or an optional preference. |
| `needs_evidence` | Perform one targeted investigation for the unresolved premise; do not automatically edit or ask the human. |

A true claim need not require a change in this PR. A necessity claim must name the unmet criterion or concrete regression/invariant—not merely a severity label. One confirming code-reality opinion cannot overrule a supported scope refutation; resolve a material disagreement through evidence.

A critical unresolved safety/correctness premise prevents readiness. Unsupported speculation does not automatically become a requirement. Preserve uncertainty honestly and distinguish these cases.

## 8. Keep a durable ledger and bounded repair batches

Store one owner ledger outside disposable worktrees using `scripts/state.py`; follow the event/CLI contract in [owner-state.md](references/owner-state.md). Track the feature contract, phase, actual sessions/branches/PRs/expected SHAs, feedback cursors, unique claims, evidence, dispositions, follow-up links, counters, and terminal outcome. The dispatcher writes the batch manifest; only the recorded owner/session writes its ledger. Do not edit either JSON file ad hoc. Store full reports separately and refer to them; do not copy transcripts into every prompt.

Identify findings by their underlying claim/root cause and affected behavior. Keep all source-comment IDs. Do not use reviewer identity, title text, or line number alone as equivalence proof.

Carry forward a supported disposition unless new evidence contradicts it, relevant code/premises changed, or requirements changed. Recheck relevant premises; a moved anchor or a new SHA alone is neither a new defect nor proof that an old defect is fixed. A new reproducer showing a previous fix still fails reopens the finding.

Defaults, shared across local and external review for the whole owner:

- Two total **review-driven repair batches**. Freeze the accepted `required_now` set before each batch; count the batch when its first code repair begins. Resume within that batch after interruption. A later accepted repair set consumes the next batch. Never append endless new claims to an open batch to evade the limit.
- Three attempts on the same failure without material progress. New discriminating evidence, a smaller reproducer, or correction of a verified cause is progress; another status check or cosmetic edit is not.
- One upfront abstraction-led planning pass and at most one conditional alternative search per feature.
- One targeted follow-up investigation per disputed claim at an unchanged premise. Persist inconclusive outcomes instead of repeatedly asking the same question.

Local red/green iterations and diagnosis within an accepted repair batch do not create extra review batches. New local-review, bot, or resumed-session invocations do not reset counters. A budget backstop selects an honest terminal outcome; it is not a routine request to replenish the same loop.

Implement the accepted batch together, add the smallest valuable proving tests, rerun affected checks, and refresh invalidated evidence. Do not weaken or suppress checks to fit a budget. Validate semantic structure in changelogs, generated registries, and other hotspots after rebases even if no merge conflict appears.

## 9. Freeze evidence and create draft PRs

Before a required independent review, finish necessary local rebases and gates. Freeze the exact target and stop editing while the gate runs.

For the mandatory aggregate stack abstraction gate, satisfy `abstraction-review/references/independent-dispatch.md` (`independent-abstraction-review/v1`) with the `stack` profile. Record the default-base ref and full tip, merge-base, stack-tip/head/tree OIDs, ordered stack OIDs and bounds, comparison semantics, exact binary diff and SHA-256. Use the appropriate canonical profile for other required targets.

Give the fresh reviewer only raw intent/criteria, repository instructions, and the frozen target/view. Enforce the required read-only capability boundary and retain the complete declared/echoed/recomputed evidence packet. Do not replace it with self-review, a generic architecture pass, or the earlier design search.

Use `pr-description` as the sole body-authoring path. Give the leaf the exact immediate base-to-head diff, observed checks/live evidence, native review report, and root dispositions/readiness decision. Preserve `ALIGNED WITH FINDINGS` as such; it is not automatically a requirement to repair optional observations, and must not be relabeled `ALIGNED`. A real blocker or incomplete canonical evidence still stops publication/readiness as applicable.

Prepare and validate a separate body for each stack member. When live validation is required, inspect a screenshot for visual behavior or retain a sanitized command/request-response transcript for nonvisual behavior, and validate with `--require-live-evidence`.

After the final aggregate snapshot and body preparation, run `gh stack submit --auto` without another rebase or content change. Verify/create draft state, correct title/base/assignee/labels, include each member's `Closes #<issue>`, and apply its own body. A singleton uses its ordinary explicit-refspec draft-PR path. Never use a cumulative stack description for every member.

Record PR URLs, immediate bases, native stack links, expected remote SHAs, worktree, and owner. Verify them against GitHub. Do not call the remote `agent-pr-review` posting workflow merely to satisfy a local gate; use its methodology. If separately asked to stage a pending review, preserve its required disclosure and explicit later-submission authorization. Do not add generated attribution to authored commits or PR bodies.

## 10. Process external feedback without restarting the feature

Collect the completed required CI/reviewer runs for the current candidate. Cover Bugbot, Droid, human suggestions, and other configured sources through the same contract. Do not push once per arriving comment or confuse an old-SHA result with current evidence. Persist a bounded wait deadline; missing required evidence is not success.

For each completed feedback batch:

1. Reconcile comments with the ledger and verify whether prior premises remain applicable.
2. If there are no new or invalidated claims, launch no adjudicator merely because another reviewer or SHA appeared.
3. Adjudicate the remaining unique claims together under section 7. Investigate only their relevant behavior, not the whole repository again.
4. Record defensible replies/no-change decisions. Deduplicate useful follow-up issues and file only the missing worthwhile concerns through the authorized templates. Record tracking failures without turning optional work into a feature-code gate.
5. If no `required_now` finding remains, make no code push just to satisfy preferences. Proceed to the final readiness check when required reviews/checks are complete.
6. If accepted repairs remain and the batch budget permits, perform one repair batch and push once. If the budget or no-progress limit is exhausted with a genuine blocker, take the terminal incomplete path.

For stacks, handle repairs bottom-to-tip. Amend the owning member, run `gh stack rebase --upstack`, and use `gh stack sync` for lease-protected chain updates. Never push a changed parent alone. Refresh expected SHAs and verify every affected descendant's latest checks and bases.

After code/history changes, invalidate every canonical packet whose binding changed and regenerate required evidence on the stable target. Cached finding dispositions are not a substitute for current-target evidence. A required fresh dispatch does not reset the ledger or authorize a new cleanup campaign.

Refresh each affected PR body against its final immediate base/head. Fetch the live body first and preserve any trailing Bugbot summary byte-for-byte; pass that snapshot as `--existing-body`. Body-only/evidence-only updates do not by themselves start a code-repair batch.

## 11. Finish or stop once

Choose and persist an explicit owner outcome:

### `review_ready`

Require all original feature criteria to be verified, a clean worktree, correct base ancestry/stack linkage, required current-SHA CI/reviewer evidence, complete current-target independent packets, and no required-now or critical unresolved finding. Every unique feedback item must have a defensible disposition. Optional suggestions/follow-ups may remain.

Mark the PRs ready without another implementation approval. Never merge. The dispatcher considers the batch finished when all owners have terminal outcomes; mixed success and failure must be reported separately.

If an associated goal exists, audit that goal's actual objective before calling its exposed completion tool. Review-ready for this feature is not proof that a broader goal is complete.

### `stopped_blocked`

Preserve an incomplete draft and record the exact unmet requirement, evidence, attempted paths, and reason work cannot proceed. Never waive gates, reclassify a real blocker to fit a budget, mark an incomplete goal complete, or ask repeatedly for another identical repair allowance.

For an associated bound goal, deliver the persisted terminal event once through the exposed `report_workflow_outcome` tool with exact owner, Pi-session, goal, event IDs, reason, and evidence references. Verify its receipt and `get_goal` show continuation suspended and the goal incomplete. If no associated goal exists, record that observation; do not create one merely to pause it. Never use a child/idle/error/sentinel notification as the terminal proof. Do not invent a `blocked` value for `update_goal`; it currently only completes goals. Missing terminal integration is a deployment prerequisite for this workflow revision, not something workers should improvise during feature work.

Ask the human only for a genuinely missing requirement/authority/access/trust decision, with the exact question and evidence. Routine file discoveries, ordinary repairs, optional feedback, and justified forecasts above 100 lines do not require permission. A terminal failure report need not be an approval request.

## 12. Resume and report

On resume, load the recorded contract, actual owner identities, ledger, counters, phase, and evidence references. Reconcile Agent Deck/GitHub/local state before acting. Continue the recorded batch/phase; do not rediscover and relaunch an already owned issue or reset history.

If another session moved an owned branch or expected remote SHA, stop before pushing and report expected versus observed identities. Never repair a shared stack one branch at a time. Stop safely on incompatible state versions rather than silently migrating or starting fresh.

Report successful and failed launches, normalized names/paths, stable owner IDs, issue chains/default bases, PRs/latest SHAs, outcomes, acceptance evidence, required repairs versus no-change/follow-ups, actual gross changed surface, review/adjudication/repair counts, and any genuine open decision. Give the scoped view command:

```bash
agent-deck -g <group>
```

Measure time to verified review-ready and necessary changed surface—not the number of bot comments “resolved.”
