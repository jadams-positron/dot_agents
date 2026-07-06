# skills

Shared agent skills for Positron.

Each skill is a `SKILL.md` collection (with any supporting files) that AI coding
agents load to extend their behavior. This repository is the source of truth;
local machines stay in sync with [gaal](https://github.com/getgaal/gaal).

## Layout

One directory per skill, each containing a `SKILL.md`:

```
<skill-name>/
  SKILL.md
```

## Syncing

[gaal](https://github.com/getgaal/gaal) installs `SKILL.md` collections from this
repo into your local agent directories. Add this repo to your gaal config
(`~/.config/gaal/config.yaml`) and run `gaal sync`.

### Example config

```yaml
schema: 1
skills:
  - source: git@github.com:jadams-positron/skills.git
    agents: ["*"]
    global: true
```

Then:

```
gaal sync
```
