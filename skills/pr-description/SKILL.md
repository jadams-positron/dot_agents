---
name: pr-description
description: Draft, refresh, or validate a PR description from a frozen diff and observed evidence, ending every draft with a pr-hygiene and distill pass so the body is plain and short. Operate as a leaf when called by another workflow, consuming its review packet without repairing code or restarting gates. Standalone outward writes perform at most one risk-required review.
---

# PR Description

Use this skill as the single source of truth for pull-request body authoring. It
supports both pre-create descriptions built from a local branch and refreshes of
an existing PR. Draft or perform the outward edit according to the authorization
already granted by the user or calling workflow. Every draft ends with the
[plain-language pass](#finish-with-the-plain-language-pass).

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

## Stay a leaf and consume review evidence

Drafting text locally requires no review gate. For an outward write, consume the root workflow's frozen target, risk tier, checks, and review packet. Low-risk work needs no independent review unless repository policy requires one. Medium- and high-risk work must carry the review evidence required by `change-control`; when that includes canonical `abstraction-review` evidence, require an `ALIGNED` packet whose declared, echoed, and recomputed target matches.
3. If caller evidence is absent or stale, return the mismatch; do not dispatch a reviewer when operating as a leaf.
   A standalone invocation may dispatch at most one risk-required reviewer with fresh context. If it fails or requests repair, stop.
4. If the report is incomplete, contaminated, or not passing, stop and return it to the root. Never repair code or restart caller gates.
5. Perform the canonical pre-use check immediately before the outward write.
   On mismatch, stop. After writing, report a target race rather than recursively refreshing.

Create new PRs as drafts. This skill never marks them ready; the calling
workflow may do that only after its remaining review, CI, and repair gates.

## Write the body

Write for a reviewer who has not seen the work. Keep the body to about 150–250
words, not counting transcripts, examples, trailers, or a preserved Bugbot block.
The body of positron-ai/mcc #1178 (`gh pr view 1178 -R positron-ai/mcc`) is the
model.

Use this shape, in this order:

1. **Why, with no heading.** Open with one short paragraph in everyday words:
   the problem, who it affects, and why it matters. Never put a heading above it
   or open with "This PR adds…".
2. **What changes.** Under a `What changes:` line, list a few outcomes for the
   people and systems affected, not the files or functions that changed. Explain
   each new term once, where it first appears. Name a deliberate non-change or
   scope boundary when a reviewer would otherwise assume it.
3. **`## What's open`.** One line per real item, each with its reason or linked
   issue: deferred work, a known limit, or what only a deploy or live check can
   show. Omit the section when nothing is open.
4. **`## Testing`.** Three to five lines on what is proven: each exact command
   or CI run, with the behavior it covers when the name does not say. Say
   `Not run` with the reason for any material gap. Never paste logs.

Write in the reader's words, not the workflow's. Caller packets carry labels the
reader never saw: phase or PR-slot labels (E1), finding IDs (R1, M12), round
names (fixes-3), and reviewer jargon (oracle, stand-in). Say what each one means,
or leave it out.

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
sections are `## How to Review` (only when a reviewer needs a starting file or an
invariant the diff does not show), `## Risk and Rollback`, `## Dependencies /
Stack`, `## Breaking Changes`, `## Deployment / Operator Notes`, and `## Out of
Scope`.

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

## Finish with the plain-language pass

End every draft with this pass, in standalone and leaf mode, before the body is
validated, returned, or published:

1. Load the `pr-hygiene` skill and apply its description rules and its "Check
   before posting" list.
2. Load the `distill` skill and run it over the body. Its preservation contract
   is the evidence set: every claim, command, result, link, and trailer survives.
   Leave a preserved Bugbot block untouched.
3. Check the result against [Write the body](#write-the-body): why first without
   a heading, outcomes rather than mechanics, no internal shorthand, one line per
   open item, three to five Testing lines, and about 150–250 words.

If either skill is unavailable, apply the rules in this file and say so. The pass
rewrites prose only; it never repairs code, adds claims, or restarts caller gates.

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
