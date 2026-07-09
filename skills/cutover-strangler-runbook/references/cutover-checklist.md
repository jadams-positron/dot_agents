# Cutover Phase-Gate Checklist + Rollback Drill

Every phase has an **entry gate** (must hold before starting) and an **exit gate**
(must hold before the next phase). No phase is skipped, no gate is waived. When any
auto-rollback trigger fires, stop, revert to the last-good state, and re-enter the
current phase's entry gate only after root-cause.

---

## Phase 0 — Prerequisites (offline verification)

Entry gate:
- [ ] `migration-worthiness-memo` said go; `migration-plan-and-discipline` ledger exists.
- [ ] `test-census-parity` passed — no test/behavior surface dropped.
- [ ] `differential-golden-harness` shows ~zero mismatch on the offline corpus.

Exit gate:
- [ ] Rollback owner + on-call named. Cutover window + soak durations agreed.

## Phase 1 — Census the live surface

Exit gate:
- [ ] Every reachable route enumerated with RPS, p50/p99 latency, error-rate baseline.
- [ ] SLOs/SLIs and current alert thresholds recorded (these become the triggers).
- [ ] Critical, non-idempotent, and high-fan-out paths flagged for extra scrutiny.
- [ ] Stateful side effects identified (writes, external calls, emails, billing) —
      these must be **suppressed** in shadow (Phase 3).

## Phase 2 — Strangler stand-up

Exit gate:
- [ ] New impl deployed as an independent upstream, reachable, at **0%** user traffic.
- [ ] Route selection sits behind the steering mechanism; old path is the default + sole authority.
- [ ] Synthetic probe (probe header) hits the new upstream and returns healthy.
- [ ] New impl emits the same request/latency/error metrics as old, same label names.

## Phase 3 — Shadow / mirror + online diff

Exit gate:
- [ ] Production traffic mirrored async to new impl; responses discarded (users unaffected).
- [ ] New impl's writes/side effects are dry-run/sandboxed — shadow must not double-write.
- [ ] Responses diffed via the `differential-golden-harness` normalization pass.
- [ ] `shadow_mismatch_total / shadow_requests_total` exported and dashboarded.
- [ ] Mismatch rate ~zero and stable across a full traffic cycle (peak + off-peak).

## Phase 4 — Arm the rollback

Exit gate:
- [ ] One-command rollback script written and committed.
- [ ] Auto-rollback triggers defined from Phase 1 SLOs (thresholds below).
- [ ] Rollback **drill** rehearsed end-to-end at 0% (see drill below) and timed.
- [ ] Alert -> rollback wiring proven (paged the on-call, or auto-fired, in the drill).

## Phase 5 — Gated rollout

Per-step gate (repeat for 1% -> 10% -> 50% -> 100%):
- [ ] Advance flag to the step's percentage, steering on a stable key.
- [ ] Soak the agreed duration (longer for the earlier, higher-risk steps).
- [ ] Success rate, error rate, p99 latency all within trigger thresholds for the whole soak.
- [ ] No trigger fired; no manual concern raised. Only then advance.
- [ ] If a trigger fired: rollback ran, incident logged, root-caused before re-advancing.

## Phase 6 — Decommission

Exit gate:
- [ ] 100% soaked clean for the full agreed window (days, not minutes).
- [ ] Old code path removed; feature flag retired; mirror torn down; dead upstream deleted.
- [ ] AGENTS.md/runbooks/dashboards updated; old alerts pruned.

---

## Gate queries (PromQL — adapt metric/label names to the repo)

```promql
# Error rate for the canaried impl (rollback if sustained above threshold)
sum(rate(http_requests_total{impl="new",code=~"5.."}[5m]))
  / sum(rate(http_requests_total{impl="new"}[5m]))

# p99 latency, new vs old (rollback on regression beyond budget)
histogram_quantile(0.99, sum by (le,impl) (rate(http_request_duration_seconds_bucket[5m])))

# Success rate (SLI) for the canaried impl
sum(rate(http_requests_total{impl="new",code=~"2.."}[5m]))
  / sum(rate(http_requests_total{impl="new"}[5m]))

# Shadow mismatch ratio — must be ~0 to exit Phase 3
sum(rate(shadow_mismatch_total[10m])) / sum(rate(shadow_requests_total[10m]))
```

Typical trigger thresholds (tune per service): error rate `> baseline + 0.5%` for
5m, p99 `> old_p99 * 1.2` for 5m, success rate `< SLO`. Evaluate against the
canaried impl only, per step.

## Traffic-mirror config

nginx — mirror to the new upstream, response ignored:

```nginx
location /api/ {
    mirror /shadow;          # async copy; client sees only the primary response
    proxy_pass http://old_upstream;
}
location = /shadow {
    internal;
    proxy_pass http://new_upstream$request_uri;
}
```

Envoy — request mirror policy on the route:

```yaml
route:
  cluster: old_upstream
  request_mirror_policies:
    - cluster: new_upstream
      runtime_fraction: { default_value: { numerator: 100, denominator: HUNDRED } }
```

The mirrored responses are discarded by the proxy. A sidecar/diff-proxy consumes
both responses, normalizes, and increments the `shadow_*` counters. Ensure the new
impl runs writes in dry-run/sandbox mode while shadowing.

## Stable-key percentage steering

Route on a hash of a stable identity so a caller does not flip impls mid-session:

```
bucket = crc32(user_id | session_id | trace_id) % 100
use_new = bucket < rollout_percent            # 1, 10, 50, 100
```

Keep an internal override: requests carrying the probe header always hit the new
impl, for verification before 1% and for post-rollback confirmation.

## Scripted one-command rollback

```bash
#!/usr/bin/env bash
# rollback.sh — flip the rewrite back to the old path in one command.
set -euo pipefail
PREV="$(flagctl get rollout_percent)"          # capture for the incident record
flagctl set rollout_percent 0                   # old path resumes immediately
flagctl get rollout_percent | grep -qx 0        # verify it took
echo "rolled back from ${PREV}% to 0% at $(date -u +%FT%TZ)"
# emit an annotation/alert so the timeline is captured
```

The rollback must be a config/flag flip (fast, no redeploy). Never make rollback
depend on rebuilding or redeploying the old impl — it stays warm the whole time.

## Rollback drill (rehearse in Phase 4, at 0%)

1. Advance the flag to 1% (or point steering at a synthetic canary), confirm the new
   impl is taking traffic on the dashboard.
2. Inject a fault (or manually breach a threshold) so a trigger condition is met.
3. Confirm the trigger fires: auto-rollback runs, or the on-call is paged and runs
   `rollback.sh`.
4. Time it: measure detection -> rollback -> recovery. Record the number.
5. Confirm the dashboard shows traffic back on the old path and metrics recovered.
6. Confirm the annotation/alert captured the event. Reset the flag to 0%.

Do not begin Phase 5 until this drill has passed and its recovery time is acceptable
against the SLO error budget.
