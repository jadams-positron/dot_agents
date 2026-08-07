# Work GitHub Issues Heartbeat

1. Drain `agent-deck inbox drain self --json` and process every completion once.
2. Run `agent-deck session children --json` and compare stable child session IDs
   with owners across every entry in `state.json.batches`.
3. Inspect output only for children that became waiting, errored, or complete.
4. Auto-respond only when `POLICY.md` makes the answer deterministic; never send
   to a running child.
5. Update only the affected batch in `state.json` and append the event and
   action to `task-log.md`. Escalate parent-linked children that have no batch.
6. Do not discover or launch new issues from a heartbeat.

Reply with `[STATUS]` when the fleet needs no decision. Emit one concise `NEED:`
line per decision or blocker that requires the user.
