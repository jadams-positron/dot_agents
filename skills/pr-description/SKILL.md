---
name: pr-description
description: Draft, verify, create, or refresh rich GitHub pull-request descriptions grounded in the exact diff and observed test evidence. Any outward PR create/edit requires matching evidence from, or dispatch of, a mandatory independent clean-context abstraction review. Use whenever a workflow opens a PR, edits a PR body, prepares stacked PR metadata, or the user asks to write, rewrite, clean up, expand, or add Summary, How to Review, Testing, or Example Usage sections to a PR description.
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
   results, CI state, relevant red/green TDD evidence, and any required live
   validation. Never claim a check was run when it was not.
5. Rebuild this evidence set after a rebase, stack sync, substantive fix, CI
   repair, or Bugbot repair before refreshing the description.
6. Before rewriting an existing PR body, fetch its live body. If Bugbot has
   appended a `<!-- CURSOR_SUMMARY -->` ... `<!-- /CURSOR_SUMMARY -->` block at
   the end, retain that exact block for preservation during the rewrite.

## Require abstraction evidence before any outward write

Drafting text locally does not require this gate. Running `gh pr create`,
`gh pr edit`, or any equivalent outward PR-body write does.

1. Use the installed `abstraction-review` skill's
   `references/independent-dispatch.md` contract
   (`independent-abstraction-review/v1`) with the `diff` profile. Freeze the
   target ref, full target-tip, merge-base, head and tree OIDs, exact
   canonical read-only binary diff and SHA-256. For an existing PR, resolve live
   endpoints from GitHub.
2. Accept caller evidence only when its complete canonical packet is `ALIGNED`
   and its declared, reviewer-echoed, and freshly recomputed target matches.
3. If evidence is absent or stale, dispatch a new reviewer under that contract.
   In Codex use `fork_turns: "none"`; another harness must provide equivalent
   fresh context and capability enforcement. Exclude the body draft,
   implementation plan, authoring conversation, prior findings, fixes, review
   output, and suspected abstractions.
4. If the report is incomplete, contaminated, or not `ALIGNED`, stop without
   publishing and return every finding to the calling workflow for repair.
   After any repair, rebase, sync, amend, or other target change, a different
   fresh reviewer must review the new exact artifact.
5. Perform the canonical pre-use check immediately before the outward write.
   On any mismatch, discard the evidence and restart. After the write, recheck;
   if the target raced, refresh the evidence and body before reporting success.

Create new PRs as drafts. This skill never marks them ready; the calling
workflow may do that only after its remaining review, CI, and repair gates.

## Write the body

Use these sections in this order.

### `## Summary`

Explain the problem and why it matters, then the implemented approach. Cover the
important control or data flow and any user, operator, API, compatibility, or
safety behavior. State meaningful scope boundaries, dependencies, and non-goals.

### `## How to Review`

Give the reviewer an efficient, concrete path through the change:

- name the files or packages to read, in order;
- identify invariants, failure paths, security boundaries, or judgment calls;
- distinguish mechanical or intentionally unchanged areas;
- provide a focused sanity check when one helps validate the behavior.

Do not write generic advice such as “review the diff.”

### `## Testing`

List exact commands and observed results. Explain which behavior, edge cases, or
contracts each check covers when the command name is not self-explanatory. Include
applicable race, security, coverage, hardware, live-environment, and red/green
evidence. Say `Not run` with the reason for any material gap.

### `## Live Evidence`

Include this section whenever deployed or runtime behavior was exercised, or
when the issue, repository, or user requires live validation. Name the
non-sensitive target or environment, the scenario exercised, and the observed
result.

- For UI or other visual behavior, embed a screenshot of the live result with
  useful alt text and a caption explaining what it proves. Include before and
  after images when the claim depends on a visual comparison.
- For nonvisual API, CLI, operator, or deployment behavior, include a fenced,
  sanitized request/response or command/output transcript instead of a terminal
  screenshot.
- Inspect every image and transcript before publishing. Exclude credentials,
  tokens, customer data, private infrastructure details, and unrelated desktop
  content. Evidence supplements the exact commands in `## Testing`; it never
  replaces them.

Use a GitHub-hosted attachment when authenticated upload is available. When the
repository already has an evidence-asset convention, a repository image may be
embedded with a relative link. Never upload evidence to an unapproved public
host. If required evidence cannot be published safely, keep the PR in draft and
report the blocker instead of silently omitting it.

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

Put issue-closing and stack trailers last in the agent-authored content, for
example:

```text
Closes #73
Stacked on #72
```

Use the repository's required closing syntax exactly.

## Preserve Bugbot's appended summary

If the live PR body ends with a Bugbot summary block, copy the complete block
into the rewritten body byte-for-byte and keep it at the end. This includes the
opening and closing markers, whitespace, links, reviewed commit SHA, and all
summary text. Never edit, reflow, regenerate, relocate, or delete any part of
it. Do not add a Bugbot summary when the live body does not already contain one.
If the exact block cannot be recovered, do not rewrite the live description.

The issue-closing and stack trailers remain last in the agent-authored content;
the preserved Bugbot block follows them because Bugbot owns that appended
content.

## Publish and verify

Write the body to a temporary file and use a body-file argument so shell quoting
cannot corrupt Markdown:

```bash
gh pr create --draft --body-file <body-file>
gh pr edit <PR> --body-file <body-file>
```

For an existing PR, first save its current live body, then pass that snapshot to
the validator so it can prove that any ending Bugbot summary is unchanged:

```bash
gh pr view <PR> --json body --jq .body > <live-body-file>
python3 scripts/validate_pr_body.py <body-file> --issue <number> \
  --existing-body <live-body-file>
```

For a new PR, run:

```bash
python3 scripts/validate_pr_body.py <body-file> --issue <number>
```

Run that command from this skill's directory, or use the script's absolute path.
Add `--require-example` when an example is applicable. After publishing, fetch the
live body and verify it still matches the intended body. Add
`--require-live-evidence` whenever live evidence is required; the validator then
requires a non-empty `## Live Evidence` section containing either an embedded
image or a fenced transcript.

Never add AI attribution, generated-summary markers, model names, or AI
co-author/reviewer trailers. The sole exception is an existing Bugbot summary
at the end of the live body: preserve it exactly as required above. Remove all
other generated summaries and attribution from the agent-authored content.
Preserve accurate human-authored context that remains useful.
