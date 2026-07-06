# dot_agents

A personal collection of AI agent skills, modeled after `~/.agents` and kept in
sync across machines with [gaal](https://github.com/getgaal/gaal).

> [!NOTE]
> This repository is **not authoritative for Positron today** — it is a personal
> setup for experimenting with shared agent skills, not an official source.

## Layout

Modeled after `~/.agents`: one directory per skill under `skills/`, each with a
`SKILL.md` (and any supporting files).

```
skills/
  <skill-name>/
    SKILL.md
```

## Skills

| Skill | Description |
|---|---|
| `cleanup-pr-description` | Rewrite a PR's description for clarity and accuracy, grounded in the actual diff, adversarially verifying every claim before updating the PR. |
| `document-distiller` | Distill messy, verbose, or draft internal docs into concise, structured, actionable output while preserving facts, constraints, and decisions. |
| `file-issue` | File GitHub issues against `positron-ai` repos and add each to an org-level GitHub Project in a single workflow. |
| `frontend-design` | Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. |
| `investigate-performance` | Turn a vague performance concern into a rigorous benchmark, profiling, race, and fuzz investigation with reproducible evidence. |

## Syncing

[gaal](https://github.com/getgaal/gaal) installs these `SKILL.md` collections into
your local agent directories. Add this repo to your gaal config
(`~/.config/gaal/config.yaml`) and run `gaal sync`.

### Example config

```yaml
schema: 1
skills:
  - source: git@github.com:jadams-positron/dot_agents.git
    agents:
      - claude-code
      - codex
    global: true
    select:
      - cleanup-pr-description
      - documentation-distiller
      - file-issue
      - frontend-design
      - investigate-performance
```

`select` matches each skill's `name` from its `SKILL.md` frontmatter — so the
`document-distiller/` directory is selected as `documentation-distiller`. Omit
`select` to install every skill in the repo.

```
gaal sync
```
