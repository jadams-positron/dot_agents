# dot_agents

A collection of AI agent skills and Agent Deck conductors, kept in sync across
machines with [gaal](https://github.com/getgaal/gaal).

## Layout

Skills follow the `~/.agents` layout. Conductors keep their source-controlled
instructions and policies under `conductors/`; Agent Deck stores their mutable
runtime state separately.

```
conductors/
  <conductor-name>/
    AGENTS.md
    POLICY.md
    HEARTBEAT_RULES.md
skills/
  <skill-name>/
    SKILL.md
```

See [conductors/README.md](conductors/README.md) for the Agent Deck design,
configured conductors, setup commands, and verification. See
[Change-Control Flow](docs/change-control-flow.md) for the shared bounded coding
workflow and root/leaf control model.

## Skills

### Migration & verification

A toolkit for large migrations and behavior-preserving refactors. They chain
together: decide with `migration-worthiness-memo`, plan and drive the port with
`migration-plan-and-discipline`, gate correctness with `semantic-delta-catalog`,
`test-census-parity`, and `differential-golden-harness`, then cut live traffic
over with `cutover-strangler-runbook`.

| Skill | Description |
|---|---|
| [`migration-worthiness-memo`](skills/migration-worthiness-memo/SKILL.md) | Decide whether a big migration or rewrite is worth doing — a go/no-go memo anchored on which bug classes the target eliminates at compile time, before any code. |
| [`migration-plan-and-discipline`](skills/migration-plan-and-discipline/SKILL.md) | Plan and enforce a large mechanical migration: a translation guide plus a cross-cutting decisions ledger, structure-preserving one-file-to-one-file porting, and staged convergence gates. |
| [`semantic-delta-catalog`](skills/semantic-delta-catalog/SKILL.md) | Catalog and burn down source→target semantic deltas (the "compiles fine, computes wrong" class), pinning each with a test that fails under the wrong behavior. |
| [`test-census-parity`](skills/test-census-parity/SKILL.md) | Prove a refactor or port lost no test coverage — a before/after census that fails on any silently deleted, skipped, or weakened test. |
| [`differential-golden-harness`](skills/differential-golden-harness/SKILL.md) | Diff old-vs-new outputs over an input corpus with a normalization pass, proving byte-for-byte parity or triaging every difference. |
| [`cutover-strangler-runbook`](skills/cutover-strangler-runbook/SKILL.md) | Cut live traffic over to a rewrite safely: dual-run, shadow-compare, a gated percentage rollout behind a flag, and scripted rollback. |

### General

| Skill | Description |
|---|---|
| [`change-control`](skills/change-control/SKILL.md) | Shared smallest-diff, risk-proportionate, single-orchestrator contract. |
| [`distill`](skills/distill/SKILL.md) | Simplify through one proportionate pass by default, capped at three. |
| [`document-research`](skills/document-research/SKILL.md) | Create or update a research document in the "Reliability & Orchestration Research" Notion database — an investigation, evaluation, spike, or benchmark rendered as a well-structured, well-cited row following the teamspace's schema and conventions. |
| [`file-issue`](skills/file-issue/SKILL.md) | File GitHub issues against `positron-ai` repos and add each to an org-level GitHub Project in a single workflow. |
| [`investigate-performance`](skills/investigate-performance/SKILL.md) | Turn a vague performance concern into a rigorous benchmark, profiling, race, and fuzz investigation with reproducible evidence. |
| [`pr-description`](skills/pr-description/SKILL.md) | Draft, validate, create, or refresh evidence-backed PR descriptions; outward writes require exact-target evidence from a mandatory independent clean-context abstraction review. |
| [`reconcile-issues`](skills/reconcile-issues/SKILL.md) | Audit a set of GitHub issues (epic children, a title prefix, a label) against the codebase — which shipped, which are superseded, which need re-scoping — then execute the closes, consolidations, epic rewrite, and native sub-issue sync on approval. |
| [`refactor-campaign`](skills/refactor-campaign/SKILL.md) | Review an entire codebase for a broad refactoring goal, validate findings into dependency-ordered work units, integrate audited worker commits locally, and independently review the final diff for abstraction alignment. |
| [`work-gh-issues`](skills/work-gh-issues/SKILL.md) | Discover actionable issues, map interdependencies into GitHub PR stacks, and fan them out into isolated Agent Deck Pi sessions with shared quality and clean-context abstraction-review gates. |
| [`work-issue`](skills/work-issue/SKILL.md) | Work a GitHub issue end to end — implement in a worktree, run an independent clean-context abstraction review and the other quality gates, open a stack-aware draft PR, squash iterative history, drive CI to green, and resolve Bugbot findings. |

## Syncing

[gaal](https://github.com/getgaal/gaal) installs these `SKILL.md` collections into
your local agent directories. Add this repo to your gaal config
(`~/.config/gaal/config.yaml`) and run `gaal sync`.

### Example config

```yaml
schema: 1
repositories:
  ~/code/github/jadams-positron/dot_agents:
    type: git
    url: git@github.com:jadams-positron/dot_agents.git
    version: main
skills:
  - source: git@github.com:jadams-positron/dot_agents.git
    agents:
      - claude-code
      - codex
    global: true
    # select: [document-research, file-issue]
```

`repositories` keeps a local working checkout of this repo; `skills` installs
the skill collections into your agent directories.

`select` matches each skill's `name` from its `SKILL.md` frontmatter. Omit
`select` to install every skill in the repo. Select deliberately: every
installed skill's description occupies the model's context in every session,
whether or not the skill runs.

```
gaal sync
```
