---
name: file-issue
description: Create one or more GitHub issues in a Positron repository, add them to an org-level GitHub Project, and complete post-create hygiene such as labels, project status/priority/size, native dependencies, and parent/sub-issue relationships. Trigger on requests like "open an issue", "file a ticket", "create some tickets for X", "add this to the MCC project", or cleanup of issues just created with this workflow. Handles single issues and small batches.
---

# File Issue

## Overview

File GitHub issues against repos in the `positron-ai` org, add each one to an org-level GitHub Project, and leave each issue with complete, verified hygiene.

## When to use

Trigger on requests like:

- "Open an issue for X"
- "File a ticket about Y"
- "Make a few tickets and add them to the MCC project"
- "Create an issue in `<repo>` for ..."

Do not trigger for general backlog triage. Post-create hygiene for issues filed by this workflow is in scope.

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
| Project | yes | Project name or number under `positron-ai`. The user often refers to "MCC" — resolve to the project number via `gh project list` (see [references/projects.md](references/projects.md)). If the new issue is a sibling or child of existing issues (follow-up, epic subtask, consolidation), match their placement instead of asking: `gh issue view <related> --json projectItems --jq '[.projectItems[].title]'` — the parent epic's membership wins. |
| Parent epic | optional | If the issue is a subtask of an epic, attach it as a **native sub-issue** (pass `--parent <epic-number>` to the script). A checklist line in the epic body is not a sub-issue relationship. |
| Title | yes | Short, imperative. Use the user's own words; do not invent. |
| Body | optional | Draft from the user's description using the template in [references/issue-template.md](references/issue-template.md). Confirm with the user before filing. |
| Labels | yes, decide | Inspect `gh label list` and apply the smallest useful existing set. Do not silently invent repository-specific labels. When the user explicitly asks for hygiene, a missing org-standard label may be created using the name, description, and color from a peer Positron repository. |
| Assignees | optional | Only if specified. |
| Status / priority / size | yes, decide | Inspect the live project fields and set every exposed field that has a defensible value. Blocked issues must use the project's `Blocked` status. Leave assignee, milestone, estimate, and dates empty when ownership or scheduling was not provided. |
| Dependencies | optional | Use native `blocked by` / `blocking` relationships only for strict prerequisites. Use issue URLs for cross-repository dependencies. |

For a *batch* of tickets, collect short descriptions for all of them up front, then draft titles + bodies together and show the user the full list before filing anything.

### 2. Resolve the project to a number

If the user gave a project name, look it up:

```bash
gh project list --owner positron-ai
```

Match against the `Title` column. The MCC project is currently titled `Mission Control Center` (number 31; it was previously `Misson Control Center (a.k.a. Orchestrator)` — titles drift, trust the live listing). Confirm the chosen project with the user if there is any ambiguity.

See [references/projects.md](references/projects.md) for more.

### 3. File and add to the project

Use the wrapper script for atomicity. Write the body to a file first to avoid shell-escaping issues:

```bash
scripts/file_issue.sh \
  --repo positron-ai/<repo> \
  --project <project-number> \
  --title "<title>" \
  --body-file /tmp/issue-body.md \
  --status Ready \
  --priority P1 \
  --size M \
  [--blocked-by <issue-number-or-url>]... \
  [--blocking <issue-number-or-url>]... \
  [--parent <epic-issue-number>]
```

The script creates the issue, then calls `issue_hygiene.sh` to add it to the project, set project fields, apply labels and native dependencies, attach a parent when requested, and verify the result. It prints the issue URL on success.

For an issue that was already created by the workflow, run the hygiene script directly:

```bash
scripts/issue_hygiene.sh \
  --issue-url https://github.com/positron-ai/<repo>/issues/<n> \
  --project <project-number> \
  --label security \
  --status Blocked \
  --priority P1 \
  --size L \
  --blocked-by https://github.com/positron-ai/<repo>/issues/<dependency>
```

For a batch, call the scripts once per issue, sequentially. Do not mark an item `Blocked` without a native dependency (or an explicit external blocker documented in the issue), and do not leave a natively blocked issue in `Ready`.

### 4. Body content

Default body sections (see [references/issue-template.md](references/issue-template.md)):

- **Context** — the situation
- **Problem / Goal** — what needs solving or doing
- **Acceptance criteria** — what "done" looks like
- **Links** — related PRs, docs, prior issues

Skip sections that do not apply. Keep bodies short — issues should fit on one screen.

### 5. Verify hygiene

Inspect every created issue before reporting completion:

```bash
gh issue view <issue-url> \
  --json labels,assignees,milestone,parent,subIssues,blockedBy,blocking,projectItems
```

Confirm:

- labels exist in the target repository and match the work;
- project membership, status, priority, and size resolved;
- native dependency direction is correct and project status agrees;
- parent/sub-issue relationships are native, not body checklists;
- unassigned, unscheduled, or milestone-free fields are intentional rather than forgotten.

## Resources

- [`scripts/file_issue.sh`](scripts/file_issue.sh) — creates an issue and delegates project/dependency hygiene
- [`scripts/issue_hygiene.sh`](scripts/issue_hygiene.sh) — applies and verifies labels, project fields, dependencies, and parent relationships for a new or existing issue
- [`references/projects.md`](references/projects.md) — how to look up org-level projects
- [`references/issue-template.md`](references/issue-template.md) — default issue body template
