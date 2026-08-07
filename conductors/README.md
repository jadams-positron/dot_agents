# Agent Deck Conductors

Conductors are persistent Agent Deck sessions that coordinate specialized
worker fleets. Their instructions and policies live in this repository; Agent
Deck owns mutable state, learnings, and logs under
`~/.local/share/agent-deck/conductor/`.

## Agent Deck Implementation

| Layer | Implementation |
|---|---|
| Runtime | Named Agent Deck conductor sessions, using Codex where the workflow depends on Codex skills. |
| Instructions | Source-controlled `AGENTS.md` files linked into each conductor by `--instructions-md`. |
| Policy | Per-conductor authorization and escalation rules linked with `--policy-md`. |
| Heartbeat | Small workflow-specific checks linked with `--heartbeat-rules-md`; Agent Deck supplies scheduling and durable inbox delivery. |
| State | Agent Deck-managed `state.json`, `LEARNINGS.md`, and `task-log.md`; concurrent work is stored in a batch-ID-keyed `batches` map, and runtime data is not committed. |
| Workers | Parent-linked Agent Deck child sessions; stable session IDs, not titles, are used for automation. |

## Conductors

| Conductor | Agent | Purpose | Primary skill | Session |
|---|---|---|---|---|
| `work-gh-issues` | Codex | Discover, plan, launch, and supervise GitHub issue and PR-stack owners. | `work-gh-issues` | `conductor-work-gh-issues` |

## Setup

Prerequisites:

- Agent Deck 1.11.0 or newer.
- `dot_agents` checked out at the path below.
- The `work-gh-issues` skill synced for Codex with `gaal sync`.

```bash
agent-deck conductor setup work-gh-issues \
  --agent codex \
  --description "Discover, launch, and supervise GitHub issue workers" \
  --instructions-md /Users/jadams/code/github/jadams-positron/dot_agents/conductors/work-gh-issues/AGENTS.md \
  --policy-md /Users/jadams/code/github/jadams-positron/dot_agents/conductors/work-gh-issues/POLICY.md \
  --heartbeat-rules-md /Users/jadams/code/github/jadams-positron/dot_agents/conductors/work-gh-issues/HEARTBEAT_RULES.md

agent-deck session start conductor-work-gh-issues
```

## Verification

```bash
agent-deck conductor status work-gh-issues --json
agent-deck session show conductor-work-gh-issues --json
agent-deck session send conductor-work-gh-issues \
  "Show available issues in positron-ai/capcom. Do not launch anything."
```

The smoke test only classifies issues. Review the result before authorizing a
launch.
