---
name: cleanup-pr-description
description: Rewrite a pull request's description for clarity and accuracy, grounded in the actual diff. Inventories the real changes via git, drafts a clean description (Summary, How to Review, Breaking Changes, Validation), and adversarially verifies every claim against the code before updating the PR. Trigger on "clean up the PR description", "fix/rewrite the PR description", "make the PR description accurate", or "add a How to Review section".
---

# Cleanup PR Description

## Overview

PR descriptions drift: they're written early, then the diff grows, findings get fixed, and
the prose no longer matches the code. This skill rewrites a PR's description so it is
**accurate to the current head** and **easy for a human to review** — without inventing
claims the diff doesn't support.

It runs a background **workflow** (`workflow.js`, bundled next to this file) that:
1. **Maps** the changed files into coherent review areas.
2. **Inventories** each area in parallel against `git show`/`git diff` — verified ground
   truth plus a list of stale/wrong claims in the current body.
3. **Drafts** a cleaned description with a `## How to Review` section for humans.
4. **Verifies** the draft with three adversarial lenses (accuracy vs git, completeness vs
   the diff stat, clarity) so nothing unsupported survives.

## When to use

- "Clean up / rewrite / fix the PR description"
- "Make the description accurate" after the branch changed
- "Add a How to Review section"

## Guardrails (read first)

- **Accuracy over preservation.** Fix every inaccuracy the inventory finds. Never claim a
  var "defaults to X" if it's actually required (`${VAR:?…}`); never assert a behavior the
  diff doesn't show. When the verifiers flag a claim, fix or drop it — don't ship it.
- **Don't fabricate validation.** Only list checks that are real and runnable. Strip
  machine-specific absolute paths (e.g. `/nix/store/.../docker` → `docker compose config`).
- **Preserve author intent + trailers.** Keep `Fixes #NNN`, `Stacked below #NNN`, and any
  intentional structure that's still correct. You're cleaning, not replacing wholesale.
- **Preserve auto-generated blocks verbatim.** Tools like Cursor Bugbot maintain a
  `<!-- CURSOR_SUMMARY -->…<!-- /CURSOR_SUMMARY -->` block in the body and regenerate it on
  each review. The draft must **exclude** it; you re-append the existing block verbatim so
  you don't clobber tool-managed content.
- **Updating the PR is outward-facing.** Show the user the cleaned description (or the key
  changes) and update with `gh pr edit` — they asked for the cleanup, so editing is in
  scope, but surface what you changed.
- **The working tree may be on another branch.** Read PR content via git against the head
  SHA, not the Read tool (the workflow agents already do this).

## Procedure

### 1. Scout inline

```bash
gh pr view <PR> --json number,title,body,headRefOid,baseRefName
git --no-pager diff origin/<base>..<head> --stat | tail -40
```

Skim the current body for obvious staleness (claims about defaults, removed features,
example output that no longer matches). This keeps you in the loop on scope.

### 2. Run the workflow

Invoke the bundled workflow (it self-resolves slug/head/base/body):

```
Workflow({ scriptPath: "<this skill dir>/workflow.js", args: { pr: <PR number> } })
```

It returns `{ draft, issues, verdicts, map, inventory }`. The full result is written to the
task output file — read it from there (the notification truncates).

### 3. Finalize the draft

- Start from `draft` (markdown body ending at the trailer).
- Apply the verifiers' `issues`: fix every **high/medium** accuracy + completeness issue;
  apply clarity fixes that genuinely help. If a verifier disagrees with reality, trust the
  code (re-check with `git show`/`git diff`) — judgment over compliance.
- Re-append the auto-generated block: extract the existing
  `<!-- CURSOR_SUMMARY -->…<!-- /CURSOR_SUMMARY -->` (or equivalent) from the **current**
  body verbatim and append it after your trailer.

### 4. Update the PR

Write the finalized body to a file, then:

```bash
gh pr edit <PR> --body-file <path>
```

Report what changed (the inaccuracies you fixed, the new How-to-Review) so the user can see
the diff in intent, not just the result.

## Notes

- The workflow's review-area clustering is generic; for a small PR it may produce 1-2 areas
  — that's fine.
- If the PR has no auto-generated tool block, skip the re-append step.
- Pairs naturally with `resolve-bugbot`: clean the description after the Bugbot loop settles
  so it reflects the final, fixed state.
