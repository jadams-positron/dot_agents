---
name: cutover-strangler-runbook
description: Use this skill to cut live production traffic from an old implementation to a rewrite safely — inventory the live surface and SLOs, stand the new service up alongside the old (strangler-fig), shadow/mirror production traffic and diff responses online, then run a gated 1%->10%->50%->100% rollout behind a feature flag with per-step soak, auto-rollback triggers, and a scripted one-command rollback before decommissioning the old path. Triggers include "roll out the rewrite", "cut over to the new service", "strangler-fig migrate", "shadow traffic to the new impl", "canary the new implementation", and "percentage rollout behind a flag".
---

# Cutover Strangler Runbook

## Overview

Cut live production traffic from an old implementation to a rewrite without a user-visible incident. This is the runtime half of a migration — the part offline verification cannot cover: real traffic mix, real load, real downstream dependencies, real failure modes. The method is the strangler-fig pattern: stand the new implementation up alongside the old, route a growing fraction of live traffic to it behind a flag, and keep the old path warm and one command away until the new one has soaked clean at 100%.

## When to use

- Triggers: "roll out the rewrite", "cut over to the new service", "strangler-fig migrate", "shadow traffic to the new impl", "canary the new implementation", "percentage rollout behind a flag".
- Enter only after the offline gates are green: `differential-golden-harness` shows ~zero mismatch on the corpus and `test-census-parity` has passed. Upstream planning lives in `migration-plan-and-discipline`; the go/no-go is `migration-worthiness-memo`.
- Do NOT use this for the go/no-go decision or the code translation itself — hand those to the skills above. Skip it entirely for a component with no live traffic or no availability contract: just deploy the replacement.

## Workflow

1. **Census the live surface and traffic shape.** Enumerate every reachable endpoint/route with its RPS, latency, and error baseline from the metrics stack — e.g. `topk(30, sum by (route) (rate(http_requests_total[7d])))`. Record current SLOs/SLIs and existing alert thresholds (they become the rollback triggers). Flag the critical, non-idempotent, and high-fan-out paths. This census defines "done" for the cutover.

2. **Stand the new impl up alongside the old (strangler-fig).** Deploy the new service as an independent upstream, reachable but receiving 0% of user traffic. Put route selection behind this repo's steering mechanism (a canary-verification runbook, a probe header, or a feature-flag/percentage service) with the old path as the default and sole authority. Confirm the new upstream is healthy under a synthetic probe before any real request reaches it.

3. **Shadow/mirror production traffic and diff online.** Mirror a copy of live requests to the new impl asynchronously — fire-and-forget; its responses are discarded and never returned to users. Diff old-vs-new responses through the normalization pass from `differential-golden-harness` so field-order/timestamp/whitespace noise is not counted, and export a `shadow_mismatch_total / shadow_requests_total` ratio metric. Drive the mismatch rate to ~zero on live traffic; shadow surfaces inputs the offline corpus missed. Do not proceed while mismatch is non-trivial.

4. **Arm the rollback before sending real traffic.** Write the scripted one-command rollback (flip the flag to 0%, old path resumes instantly) and define auto-rollback triggers from the step-1 SLOs: error-rate, p99 latency, and success-rate thresholds evaluated per step. Rehearse the rollback drill (see the reference) end-to-end at 0% so the command and the alert wiring are proven cold, before any user is exposed.

5. **Gated percentage rollout.** Advance the flag 1% -> 10% -> 50% -> 100%, steering on a stable key (user/session hash) so a caller sticks to one impl across requests. Verify internally via the probe header first. Hold a defined soak at each step, watching success rate, error rate, and latency against the triggers; advance only when the step's exit gate is met. Any trigger firing runs the scripted rollback — automatically or on-call — and reverts to the last-good percentage.

6. **Decommission the old path after a full soak at 100%.** Only once 100% has soaked clean for the agreed window: remove the old code path, retire the flag and the mirror, and delete the dead upstream. Update the project's AGENTS.md/runbooks. Until that window closes, keep the old path warm.

## Gate

Each phase has an entry gate; do not advance without meeting it. Shadow mismatch ~zero gates the rollout; each rollout step's soak-plus-triggers gate the next step; a clean 100% soak gates decommission. Any auto-rollback trigger at any step is a hard stop that reverts to the last-good state and blocks re-advance until root-caused. The full checkbox checklist and the rollback drill are in the reference.

## References

- `references/cutover-checklist.md` — the phase-gate checklist (entry/exit gate per phase), the rehearsable rollback drill, and concrete snippets: PromQL gate queries, traffic-mirror config (nginx/Envoy), stable-key percentage steering, and the scripted one-command rollback.
