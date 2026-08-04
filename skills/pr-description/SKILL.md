---
name: pr-description
description: Draft, verify, create, or refresh rich GitHub pull-request descriptions grounded in the exact diff and observed test evidence. Use whenever a workflow opens a PR, edits a PR body, prepares stacked PR metadata, or the user asks to write, rewrite, clean up, expand, or add How to Review, Summary, Testing, or Example Usage sections to a PR description.
---

# PR Description

Use this skill as the single source of truth for pull-request body authoring. It
supports both pre-create descriptions built from a local branch and refreshes of
an existing PR. Draft or perform the outward edit according to the authorization
already granted by the user or calling workflow.

## Build the evidence set

1. Resolve the exact base and head refs. For a stacked PR, use its immediate
   parent branch as the base; never describe the cumulative stack diff.
2. Read the linked issue, acceptance criteria, repository instructions, and PR
   template when present.
3. Inspect the complete base-to-head diff and enough surrounding code to explain
   control flow, contracts, failure paths, and deliberate non-changes.
4. Collect observed evidence only: exact test commands and outcomes, review
   results, CI state, and relevant red/green TDD evidence. Never claim a check
   was run when it was not.
5. Rebuild this evidence set after a rebase, stack sync, substantive fix, CI
   repair, or Bugbot repair before refreshing the description.

## Write the body

Use these sections in this order.

### `## How to Review`

Give the reviewer an efficient, concrete path through the change:

- name the files or packages to read, in order;
- identify invariants, failure paths, security boundaries, or judgment calls;
- distinguish mechanical or intentionally unchanged areas;
- provide a focused sanity check when one helps validate the behavior.

Do not write generic advice such as “review the diff.”

### `## Summary`

Explain the problem and why it matters, then the implemented approach. Cover the
important control or data flow and any user, operator, API, compatibility, or
safety behavior. State meaningful scope boundaries, dependencies, and non-goals.

### `## Testing`

List exact commands and observed results. Explain which behavior, edge cases, or
contracts each check covers when the command name is not self-explanatory. Include
applicable race, security, coverage, hardware, live-environment, and red/green
evidence. Say `Not run` with the reason for any material gap.

### `## Example Usage`

Include this section when the change has a user-, operator-, configuration-,
CLI-, API-, UI-, Slack-, migration-, or deployment-facing surface. Prefer the
smallest realistic example that makes the change reviewable:

- configuration before/after, including defaults and required values;
- a command and representative output;
- an API request/response;
- the old and new workflow or observable behavior.

Omit the section for purely internal changes with no meaningful usage example.
Never invent configuration keys, output, or behavior.

## Add optional sections only when useful

Place optional detail after the core sections and before closing trailers. Common
sections are `## Risk and Rollback`, `## Dependencies / Stack`, `## Breaking
Changes`, `## Deployment / Operator Notes`, and `## Out of Scope`.

Put issue-closing and stack trailers last, for example:

```text
Closes #73
Stacked on #72
```

Use the repository's required closing syntax exactly.

## Publish and verify

Write the body to a temporary file and use a body-file argument so shell quoting
cannot corrupt Markdown:

```bash
gh pr create --body-file <body-file>
gh pr edit <PR> --body-file <body-file>
```

Before publishing, run:

```bash
python3 scripts/validate_pr_body.py <body-file> --issue <number>
```

Run that command from this skill's directory, or use the script's absolute path.
Add `--require-example` when an example is applicable. After publishing, fetch the
live body and verify it still matches the intended body.

Never include AI attribution, generated-summary markers, model names, or AI
co-author/reviewer trailers. When refreshing an existing body, remove generated
summary blocks and attribution instead of preserving them. Preserve accurate
human-authored context that remains useful.
