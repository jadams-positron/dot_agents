# Work GitHub Issues Heartbeat

1. Drain `agent-deck inbox drain self --json`; reconcile each event ID once.
2. Compare parent-linked children with stable owner IDs in the recorded batch manifests. Unknown ownership requires evidence, not a guessed assignment.
3. Inspect output/owner state only for newly waiting, errored, idle, or completed children. A completion sentinel or successful wait does not prove feature success.
4. Auto-answer only a nonterminal waiting owner when `POLICY.md` determines the answer. Never send to a running owner, reopen a settled claim, reset counters, or nudge `stopped_blocked` work.
5. Record the affected outcome/event and evidence pointer once in the supervision summary and `task-log.md`. Do not edit worker ledgers or branches.
6. Do not discover/launch new issues or replacement workers during a heartbeat.

Use `[STATUS]` when no new decision is needed. Emit one concise blocker/decision report per terminal event; repeated notifications do not produce repeated approval requests. Distinguish verified `review_ready`, honest `stopped_blocked`, and unverified runtime notifications.
