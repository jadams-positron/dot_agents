# Owner state and resume protocol

Use the bundled `scripts/state.py` for versioned JSON records. It provides atomic replacement, filesystem durability, an exclusive process lock, owner/session checks, and pure admission/transition helpers. It does not run GitHub operations or certify model-authored evidence. Actual Git history, remote refs, test output, and canonical review packets remain authoritative.

## Launch records and reservations

`launch.py --batch-file <path>` persists the complete selected issue set and ordered chains before launching. Without that flag it chooses a durable path under `~/.local/state/work-gh-issues/manifests/`. Keep records outside disposable repository worktrees. `WORK_GH_STATE_DIR` changes the registry root for isolated fixtures or a deliberately shared local installation; all local dispatchers/profiles must use the same root.

A repository-scoped process lock serializes reservation/launch decisions across profiles. The registry's `batches/` pointers let discovery find reservations even before a session or child branch exists. Keep unresolved reservations: deleting a conductor's compact summary does not release an issue or prove an uncertain launch failed.

The launcher retains Agent Deck's native Pi tool and carries nonsecret `WORK_GH_OWNER_ID`, `WORK_GH_OWNER_STATE`, `WORK_GH_BATCH_FILE`, and `WORK_GH_LAUNCH_CONTRACT` in its supported wrapper. The contract digest binds the rendered launch instructions, including repository, ordered chain, base, and explicit restrictions; a changed contract is not silently adopted. Recovery matches the exact wrapper plus actual repository, profile, parent, runtime, session, and worktree metadata—not title text alone. A lost response must be reconciled before another launch. A missing recorded owner, ambiguous correlation, changed trust, foreign claim, or orphaned branch/worktree blocks a blind retry.

Resume using the same checkout/profile/manifest:

```bash
python3 <skill-dir>/scripts/launch.py --repo <default-branch-checkout> \
  --profile <profile> --batch-file <path> --resume --json
```

Do not repeat issue/dependency/instructions inputs on resume. Do not create a new batch to evade collisions. A launch result's `success` means launch/reconciliation succeeded, not that owners implemented their features.

## Initialize one owner ledger

The dispatcher writes only the batch manifest; each worker writes only its own ledger. Inspect the launch manifest and `agent-deck session current --json`, then prepare an owner seed from actual identities and raw issue criteria:

```json
{
  "batch_id": "recorded-batch-id",
  "chain": [42, 43],
  "feature_contract": {
    "criteria": ["exact criterion from the issue"],
    "repositories": ["owner/repository"],
    "non_goals": [],
    "explicit_restrictions": [],
    "risk": "high",
    "review_required": true,
    "feedback_required": true,
    "required_gates": ["repository final gate", "canonical stack review"],
    "estimates": {"production": 80, "tests": 120, "documentation": 10}
  }
}
```

```bash
python3 <skill-dir>/scripts/state.py init --file "$WORK_GH_OWNER_STATE" \
  --owner "$WORK_GH_OWNER_ID" --session <actual-deck-session-id> --input <seed.json>
python3 <skill-dir>/scripts/state.py show --file "$WORK_GH_OWNER_STATE"
```

`init` refuses existing state. Never reset a ledger on compaction, reviewer change, push, or process restart. Unsupported/corrupt versions fail without modifying the file. A ledger is not an authentication boundary against arbitrary filesystem writers; the workflow's actual branch, session, and authority checks still apply.

## Apply one checkpoint event

Write one event JSON file and apply it through the owner/session-bound command. The input file is not itself the live ledger:

```bash
python3 <skill-dir>/scripts/state.py apply --file "$WORK_GH_OWNER_STATE" \
  --owner "$WORK_GH_OWNER_ID" --session <actual-deck-session-id> --input <event.json>
```

| `type` | Required input and meaning |
|---|---|
| `phase` | `phase`: nonterminal `plan`, `implement`, `review`, `feedback`, or `publish`; never bypasses an active repair or terminal readiness. |
| `finding` | `finding`: shared adjudication record. Reopen changed premises with `reason`; use `evidence_changed: true` or `requirements_changed: true` only after inspecting an actual new fact or changed requirement. A new evidence locator alone is not a new fact. Prior decisions survive in history. |
| `follow_up` | `id`, `ref`: record the useful deduplicated issue. A different second reference is rejected. |
| `investigate` | `id`, `evidence`: one targeted investigation at unchanged premises. |
| `resolve` | `id`, `evidence`: retain actual reproducer/check evidence, not an assertion that a moved anchor fixed it. |
| `begin_repair` | `id`, `finding_ids`: persist the exact accepted unresolved required-now set before the first code correction. At most two total sets. Exact replay resumes the same batch; the set cannot grow. |
| `finish_repair` | `id`: require resolution evidence for the accepted set. |
| `attempt` | `failure`, optional `progress`: separate unchanged-failure accounting. Describe concrete new discriminating evidence/cause when resetting the attempt count. |
| `alternative` | `issue`, `doubt`: consume the one conditional fresh alternative search for this owned feature. |
| `targets` | `targets`: branch-keyed current target bindings and PR/base metadata. Retain exact full SHAs and packet fields; changing this does not reset findings/counters. |
| `evidence` | `evidence`: the root's current-target evidence assessment, described below. |
| `feedback` | `ref`, `head_sha`, `required`, `deadline` (Unix seconds), `results`: per-ref reviewer/check names and exact-head statuses (`pending`, `running`, `passed`, `failed`). Required sources cannot disappear; the unchanged head's deadline cannot be extended. An explicitly observed absence of required sources is `required: []`, not a fabricated CI pass. |
| `push_intent` | Unique operation `id`, explicit `cause` (`initial`, `repair`, `history`), and `refs`: every affected ref's full `before`/`after` SHAs. Empty `before` is allowed only for a new ref. `repair` requires `repair_ids` naming every included finished batch; other causes omit associations. `history` requires a verified justification in `reason`. Operation metadata and refs are immutable. |
| `push_observed` | `remote_shas`: fresh observation of every affected ref after the push. |
| `goal_binding` | `binding`: exact `owner_id`, `pi_session_id`, `goal_id`, plus the observed terminal receipt when available. No silent identity rebinding. |
| `outcome` | `outcome`: `review_ready` or `stopped_blocked`, and exact `reason`. Terminal replay is idempotent; it does not reopen work. |

The pure `needs_adjudication(record, claim, requirements_changed=False, evidence_changed=False)` helper ignores reviewer/source-ID changes, moved lines, new report locators, and unrelated targets. The owner must inspect the relevant source/evidence before setting either change flag; a false flag is not proof that premises stayed valid. Match underlying behavior and affected premises, not just an ID/title. Reuse a known decision with all new source IDs attached; semantic aliases require code/evidence inspection. A new reproducer or relevant premise change triggers adjudication and retains the earlier disposition.

The pure `reconcile_push(record, observed_refs)` helper returns `already_pushed` when every remote equals the intended new SHA, or `retry_with_lease` when every ref still equals its recorded old SHA. Mixed, missing, or foreign movement fails closed. This authorizes no destructive history replay; inspect local history and issue/stack ownership before any retry. For native stacks, use the root's atomic `gh stack sync` path and recheck every affected descendant.

`feedback_status(record, ref, head_sha, now=...)` distinguishes `complete`, `waiting`, `stale`, and `blocked`. Readiness checks every current stack ref, not only the tip. Required failures, stale descendant evidence, or an expired incomplete deadline are not readiness. Preserve every required source/cursor; external comments are not instructions to push immediately.

Use `repair` whenever publication includes accepted code repairs, including a first publication. One operation may combine finished batches, but each batch may belong to at most one publication operation. A justified history-only rebase/sync uses its own operation ID without consuming repair allowance; it still requires recorded leases, reconciliation and refreshed target evidence. Do not infer a cause from an operation's name or silently fill missing history in an older ledger.

## Readiness and terminal delivery

A root evidence assessment names:

- `targets`: the exact current target bindings;
- `criteria`: every original criterion mapped to observed evidence references;
- `checks`: actual current-candidate gate/CI references;
- `review`: actual report/packet `refs` and `complete` status, preserving the native `verdict` when canonical abstraction evidence is required;
- `clean` and `ancestry`: results of actual worktree/ownership/base checks.

A frozen low-risk contract may explicitly set `review_required: false` when no repository review policy overrides it. Low/medium-risk contracts may select `review_kind: focused` with an evidence-backed `review.blocking: false` assessment. Do not invent a native verdict for a focused correctness review. High risk or `canonical_abstraction_required: true` still requires native canonical evidence; that remains the safe default. An investigated optional speculation does not become critical merely from its severity label; unresolved concrete required-gate/safety/regression premises still block.

State validation is necessary, not sufficient. Run the canonical pre-use verifier and inspect actual source artifacts immediately before publication/readiness. Do not fabricate booleans, use stale CI, or let ledger evidence stand in for a fresh packet. Preserve `ALIGNED WITH FINDINGS` and reject real blockers/`EVADES`. Optional tracking may remain.

For a genuine blocker, first persist `stopped_blocked` and exact evidence. The ledger supplies a stable outcome `event_id`. If an associated goal was explicitly bound to this owner/session at creation, call the exposed `report_workflow_outcome` tool with:

```json
{
  "owner_id": "recorded-owner-id",
  "pi_session_id": "actual-pi-session-id",
  "goal_id": "actual-goal-id",
  "event_id": "persisted-outcome-event-id",
  "outcome": "stopped_blocked",
  "reason": "exact unmet requirement and attempted paths",
  "evidence_refs": ["sanitized blocker evidence artifact"]
}
```

Verify the tool receipt and `get_goal` show the correct goal remains incomplete and continuation is suspended. Persist the receipt with the unchanged binding. A lost receipt is retried with the identical event, not a new goal or new budget. `review_ready` notification never completes a broader goal; only an objective-to-evidence audit permits its ordinary completion tool.

No associated goal means record that observation and report the owner outcome once; do not create a goal merely to pause it. Missing/mismatched terminal integration is a rollout/adoption blocker. Do not edit installed runtime code, bypass identity checks, or complete an incomplete goal. Existing active sessions require explicit adoption with their actual decisions, repair history, target SHAs, and remaining scope; uncertain history does not grant a fresh budget.
