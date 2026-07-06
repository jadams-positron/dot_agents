# Issue body template

A short, opinionated default. Skip any section that does not apply — empty headers are noise. Keep the whole body short enough to fit on one screen; if it does not, the ticket probably wants splitting.

## Sections

```markdown
## Context

<1–3 sentences on the situation. What system, what state, what prompted this.>

## Problem / Goal

<What needs solving or doing. State it plainly. If it is a bug, describe the wrong behavior. If it is work, describe the desired end state.>

## Acceptance criteria

- <Concrete, checkable condition 1>
- <Concrete, checkable condition 2>

## Links

- <PRs, prior issues, docs, Slack threads, dashboards>
```

## Guidance

- **Title**: imperative and specific. `Fix Caddy 502 on cold start` beats `Caddy issue`. `Add Prometheus scrape for andoria-t01` beats `Monitoring`.
- **Context**: only what a teammate needs to load the situation. Do not recap the codebase.
- **Problem / Goal**: one is enough. Bug → Problem. Work → Goal.
- **Acceptance criteria**: prefer 2–4 concrete bullets over a paragraph. They double as the PR checklist.
- **Links**: hyperlinks, not bare URLs where reasonable.

## Examples

### Bug

```markdown
## Context

`platformd` on `andoria-t01` is failing to flash card 2 after the 12.9 CUDA upgrade.

## Problem

`pho cards flash` returns exit 1 with `usb device busy`. Other cards on the same host flash fine. Reproduces on every attempt since 2026-04-29.

## Acceptance criteria

- `pho cards flash --slot 2` succeeds on andoria-t01
- Root cause documented in the issue or a follow-up

## Links

- platformd commit 8fd33b4
- Slack: #lab-ops 2026-04-30 thread
```

### Task

```markdown
## Context

We added Caddy 2.11 in labmgr/core (commit c06e3d3) but the observability stack still scrapes the old metrics endpoint shape.

## Goal

Update Prometheus scrape config so Caddy 2.11 metrics flow into Grafana without gaps.

## Acceptance criteria

- `caddy_*` series present in Prometheus
- Existing dashboards continue to render

## Links

- labmgr/observability/prometheus.yml
```
