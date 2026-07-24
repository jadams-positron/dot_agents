# dot_agents

A collection of AI agent skills, modeled after `~/.agents` and kept in sync
across machines with [gaal](https://github.com/getgaal/gaal).

## Layout

Modeled after `~/.agents`: one directory per skill under `skills/`, each with a
`SKILL.md` (and any supporting files).

```
skills/
  <skill-name>/
    SKILL.md
```

## Skills

### Migration & verification

A toolkit for large migrations and behavior-preserving refactors. They chain
together: decide with `migration-worthiness-memo`, plan and drive the port with
`migration-plan-and-discipline`, gate correctness with `semantic-delta-catalog`,
`test-census-parity`, and `differential-golden-harness`, then cut live traffic
over with `cutover-strangler-runbook`.

| Skill | Description |
|---|---|
| `migration-worthiness-memo` | Decide whether a big migration or rewrite is worth doing — a go/no-go memo anchored on which bug classes the target eliminates at compile time, before any code. |
| `migration-plan-and-discipline` | Plan and enforce a large mechanical migration: a translation guide plus a cross-cutting decisions ledger, structure-preserving one-file-to-one-file porting, and staged convergence gates. |
| `semantic-delta-catalog` | Catalog and burn down source→target semantic deltas (the "compiles fine, computes wrong" class), pinning each with a test that fails under the wrong behavior. |
| `test-census-parity` | Prove a refactor or port lost no test coverage — a before/after census that fails on any silently deleted, skipped, or weakened test. |
| `differential-golden-harness` | Diff old-vs-new outputs over an input corpus with a normalization pass, proving byte-for-byte parity or triaging every difference. |
| `cutover-strangler-runbook` | Cut live traffic over to a rewrite safely: dual-run, shadow-compare, a gated percentage rollout behind a flag, and scripted rollback. |

### General

| Skill | Description |
|---|---|
| `cleanup-pr-description` | Rewrite a PR's description for clarity and accuracy, grounded in the actual diff, adversarially verifying every claim before updating the PR. |
| `document-distiller` | Distill messy, verbose, or draft internal docs into concise, structured, actionable output while preserving facts, constraints, and decisions. |
| `file-issue` | File GitHub issues against `positron-ai` repos and add each to an org-level GitHub Project in a single workflow. |
| `frontend-design` | Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. |
| `investigate-performance` | Turn a vague performance concern into a rigorous benchmark, profiling, race, and fuzz investigation with reproducible evidence. |
| `reconcile-issues` | Audit a set of GitHub issues (epic children, a title prefix, a label) against the codebase — which shipped, which are superseded, which need re-scoping — then execute the closes, consolidations, epic rewrite, and native sub-issue sync on approval. |

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
    select:
      - cleanup-pr-description
      - cutover-strangler-runbook
      - differential-golden-harness
      - documentation-distiller
      - file-issue
      - frontend-design
      - investigate-performance
      - migration-plan-and-discipline
      - migration-worthiness-memo
      - reconcile-issues
      - semantic-delta-catalog
      - test-census-parity
```

`repositories` keeps a local working checkout of this repo; `skills` installs
the skill collections into your agent directories.

`select` matches each skill's `name` from its `SKILL.md` frontmatter — so the
`document-distiller/` directory is selected as `documentation-distiller`. Omit
`select` to install every skill in the repo.

```
gaal sync
```
