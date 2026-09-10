# Work GitHub Issues rollout

Ship the workflow as a coordinated source bundle, not a Markdown-only upgrade. See [the owner protocol](../skills/work-gh-issues/references/owner-state.md), [shared dispositions](../skills/change-control/references/feedback-disposition.md), and [pressure scenarios](../skills/work-gh-issues/tests/scenarios.md).

## Compatibility set

Record the verified commit IDs, dirty-file baseline, installed resource inventory/hashes, test artifacts, and rollback versions before rollout:

| Source | Required surface |
|---|---|
| `jadams-positron/dot_agents` | Shared policy/reference, issue/stack skills, launcher/discovery, state schema **1**, PR-description, conductor policies |
| `positron-ai/llm-toolbox` | Review result schema **4** across producers/validators, native canonical evidence unchanged, abstraction planning and required-now-only `fix-all` |
| `jadams-positron/llm-toolbox` | Quota-free, disposition-based `review-pr` |
| `coctostan/pi-superpowers` (unchanged) | Consume-only upstream dependency; owned [caller rules](../skills/change-control/references/upstream-skills.md) govern execution and feedback |
| `jadams-positron/pi-codex-goal` | Source-owned `report_workflow_outcome`, creation-time binding and persisted idempotent pause receipts; stock **0.3.0 alone is insufficient** |

Pin reviewed Git commits, not a moving branch or only the package version. Superpowers is **consume-only**: record its unchanged upstream revision, do not publish or install a workflow-specific fork, and keep compatibility rules in the owned callers. The canonical abstraction contract stays `independent-abstraction-review/v1`; do not replace independently maintained adapters or overwrite unrelated local dispatch work. Preserve existing source changes and installed helpers outside the bundle's actual diff.

State uses separate writer-owned records deliberately: the dispatcher owns the batch manifest/reservations, while each worker owns its ledger. One persistence helper implements validation/locking/atomic replacement for both. This avoids multiwriter overwrites without introducing a new scheduler, generic workflow language, or parallel source of branch truth.

## Verify before installation

From each source's `skills/` directory:

```bash
python3 -m unittest discover -s work-gh-issues/scripts -p 'test_*.py'
python3 -m unittest discover -s pr-description/scripts -p 'test_*.py'
```

From `agent-pr-review/`, run all existing `test_*.js` suites and `python3 -m unittest -v test_post_pending_review.py`. From goal source, run `npm ci --ignore-scripts` and `npm run verify`. Run owned companion checks and fresh-context S1–S8 decisions with the unchanged upstream Superpowers texts plus the owned caller contract. Preserve red/green results; a word-presence test is not a behavioral rollout proof.

Required isolated qualification:

- Real Git/Agent Deck singleton, two-member stack, and independent owner. Exercise partial and lost launch responses, persisted reservations, restart, actual normalized metadata, changed worktree-script trust, and foreign remote movement. Stubbed GitHub discovery is not live GitHub evidence.
- Real interactive Pi `/goal` creation, review-ready notification plus objective audit, and genuine blocked suspension. Verify owner/session/goal binding, retained incomplete state, receipt replay, restart/compaction, and absence of repeated continuation turns. `pi -p` or a mocked controller alone does not prove TUI behavior.
- Required canonical review of the stable exact tooling candidate, with native report, effective read-only capabilities, provenance, complete target echo, and live pre-use verification.

A disposable GitHub PR smoke is separately opt-in; never mutate production issues/PRs to manufacture coverage. Distinguish tabletop, unit-fake, real Agent Deck, real TUI, and live GitHub artifacts in the release evidence.

## Preview and stage GAAL safely

Inspect the installed `gaal sync --help` first. Use an explicit reviewed config with only the intended skill sources/selections; exclude incidental repository/MCP/content updates. Sources must be local **`.../skills` subdirectories**, not Git roots: resolving a Git root can hard-reset it. Do not refresh a dirty source or change existing worker branches.

```bash
gaal --config <reviewed-skills-only.yaml> sync --dry-run
gaal --config <reviewed-skills-only.yaml> --sandbox <disposable-directory> sync
```

Compare staged files with the selected source revisions and retained installation baseline, including adapters, validators, helpers, and references—not just `SKILL.md`. Preserve nonselected resources. `--prune` owns non-hidden target entries: do not use it with a partial selection. The generic target installs into `~/.agents/skills`; keep Claude's target in the same compatible bundle where configured.

Qualification must not overwrite installed distribution copies or global settings. After explicit activation authorization, synchronize from the reviewed authoritative sources with the same bounded configuration and recheck installed hashes/versions. Preserve unrelated source modifications; do not install an older whole skill directory over newer uncommitted helper work.

## Stage Pi packages without duplicate goals

Use a disposable `PI_CODING_AGENT_DIR`, project, and session directory for qualification; do not reuse an active session or automatically migrate its contract. Local package paths allow source-owned testing without editing installed `dist/` files:

```bash
PI_CODING_AGENT_DIR=<disposable-config> pi install <verified-goal-source-path>
PI_CODING_AGENT_DIR=<disposable-config> pi install git:github.com/coctostan/pi-superpowers@<recorded-upstream-commit>
PI_CODING_AGENT_DIR=<disposable-config> pi list
```

Build the source package through its normal build/verify path. For a shipped installation, use the reviewed commit syntax `git:github.com/jadams-positron/pi-codex-goal@<verified-commit>` while retaining upstream-only Superpowers consumption. Replace the previous goal package entry using supported package/config commands; do not append a second differently identified goal package to global/project settings. Verify one active goal extension exposes the exact outcome tool. Package names alone do not prove code identity.

Default activation to **new owner sessions** with creation-time `WORK_GH_OWNER_ID` binding. A legacy/unowned active goal cannot be adopted merely by passing its ID to the terminal tool. An explicit adoption must preserve actual owner identities, criteria, consumed repair batches, findings/dispositions, expected remote SHAs, and remaining scope. If history or binding cannot be established, keep the old contract and record the blocker; do not grant a fresh budget or reset a state file.

A terminal owner is not automatically reopened by an idle event or conductor restart. An operator must resolve any real authority/access/history decision before arranging an explicitly authorized resumption/adoption. Goal receipt replay does not grant a new repair allowance.

## Rollback and recovery

Retain the exact previous source/package refs and installed inventory. Pause new launches before switching bundles. Existing owners retain their original compatible state/contract; do not silently downgrade schema **1** records or feed schema **4** review results to older consumers. A corrupt, missing, or incompatible record is preserved and blocks replay.

Keep unresolved launch reservations and owner evidence even after archiving a conductor summary. To retire/recover a reservation, first reconcile actual sessions, all chain members, worktrees, branches, PRs, and pending remote writes. Record the explicit operator decision and retain a backup; deleting a pointer is not evidence that a lost launch failed.

Measure elapsed delivery time, handwritten churn versus estimates, review-induced scope growth, raw comments versus unique claims, adjudication calls, repair batches/pushes, reopening reasons, and repeated terminal events. Success is verified feature delivery—not the number of suggestions obeyed or tickets created.
