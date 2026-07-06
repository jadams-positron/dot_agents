---
name: file-issue
description: This skill should be used when the user wants to file one or more GitHub issues against a Positron repository and add them to a GitHub Project at the positron-ai org level. Triggered by phrases like "open an issue", "file a ticket", "create some tickets for X", or "add this to the MCC project". Handles single issues and small batches.
---

# File Issue

## Overview

File GitHub issues against repos in the `positron-ai` org and add each one to an org-level GitHub Project (e.g. the MCC project) in a single workflow.

## When to use

Trigger on requests like:

- "Open an issue for X"
- "File a ticket about Y"
- "Make a few tickets and add them to the MCC project"
- "Create an issue in `<repo>` for ..."

Do not trigger for issue *triage* (commenting, closing, labeling existing issues) — only for creating new ones.

## Prerequisites

Before filing, verify the gh CLI has the `project` scope (required for org-level Projects v2):

```bash
gh auth status
```

If the output does not list `read:project` (or `project`), instruct the user to run the following themselves — it is interactive:

```bash
gh auth refresh -s project
```

## Workflow

### 1. Gather inputs from the user

Ask for any of these the user has not already provided. Batch the questions in a single message — do not ask one at a time.

| Field | Required | Notes |
|-------|----------|-------|
| Repo | yes | `owner/repo`. If the user names a Positron repo without owner (e.g. `platformd`), assume `positron-ai/<repo>`. |
| Project | yes | Project name or number under `positron-ai`. The user often refers to "MCC" — resolve to the project number via `gh project list` (see [references/projects.md](references/projects.md)). |
| Title | yes | Short, imperative. Use the user's own words; do not invent. |
| Body | optional | Draft from the user's description using the template in [references/issue-template.md](references/issue-template.md). Confirm with the user before filing. |
| Labels | optional | Only if the user specifies them. Do not invent labels — `gh` fails on labels that do not exist in the target repo. |
| Assignees | optional | Only if specified. |

For a *batch* of tickets, collect short descriptions for all of them up front, then draft titles + bodies together and show the user the full list before filing anything.

### 2. Resolve the project to a number

If the user gave a project name, look it up:

```bash
gh project list --owner positron-ai
```

Match against the `Title` column. The MCC project is currently titled `Misson Control Center (a.k.a. Orchestrator)` (note the typo). Confirm the chosen project with the user if there is any ambiguity.

See [references/projects.md](references/projects.md) for more.

### 3. File and add to the project

Use the wrapper script for atomicity. Write the body to a file first to avoid shell-escaping issues:

```bash
scripts/file_issue.sh \
  --repo positron-ai/<repo> \
  --project <project-number> \
  --title "<title>" \
  --body-file /tmp/issue-body.md
```

The script runs `gh issue create`, captures the resulting issue URL, then runs `gh project item-add` to attach it to the project. It prints the issue URL on success.

For a batch, call the script once per issue, sequentially. After all are filed, report the URLs back to the user as a list.

### 4. Body content

Default body sections (see [references/issue-template.md](references/issue-template.md)):

- **Context** — the situation
- **Problem / Goal** — what needs solving or doing
- **Acceptance criteria** — what "done" looks like
- **Links** — related PRs, docs, prior issues

Skip sections that do not apply. Keep bodies short — issues should fit on one screen.

## Resources

- [`scripts/file_issue.sh`](scripts/file_issue.sh) — creates an issue and adds it to a project in one call
- [`references/projects.md`](references/projects.md) — how to look up org-level projects
- [`references/issue-template.md`](references/issue-template.md) — default issue body template
