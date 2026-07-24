---
name: reconcile-issues
description: This skill should be used when auditing a set of GitHub issues (an epic's children, a title prefix, a label, a stale backlog) against the current codebase to determine which are already implemented, superseded, or in need of re-scoping — and then, on approval, executing the cleanup — closing with rationale comments, consolidating residual scope into new issues, rewriting epic bodies, and syncing native sub-issues. Triggers include "which of these issues can be closed", "reconcile the backlog against the code", "audit the epic's children", "are these issues still valid", "close out the done ones".
---

# Reconcile Issues

## Overview

Reconcile a set of GitHub issues against what actually shipped. Three phases: **audit** (gather evidence), **decide** (the owner rules), **execute** (clean up). Never skip the decide gate — closing and re-scoping are product decisions, and an issue's author may know reasons the code cannot show.

## Phase 1 — Audit (read-only)

1. **Enumerate the set**: `gh issue list --repo <o/r> --state open --search "<prefix> in:title"`, a label filter, or an epic's native sub-issues (see `references/gh-mechanics.md`). Include near-misses that reference the same subsystem — they often share residual scope.
2. **Pin ground truth**: `git fetch origin <default-branch>` and audit against `origin/<default-branch>` only — never the working tree. A feature-branch checkout lags the default branch and yields false "this consumer still exists" claims; when in doubt read files via `git show origin/<branch>:<path>` and confirm history with `git log origin/<branch> -- <path>`.
3. **One auditor per issue** (fan out with the Workflow or Agent tool when available; sequentially otherwise):
   - Read the FULL body and every comment — comments frequently re-scope an issue after filing.
   - Decompose the issue into concrete deliverables: each verb, flag, file deletion, doc, CI job it asks for.
   - Hunt each deliverable: grep the tree, `git log origin/<branch> -i --grep=<term>`, `gh pr list --state all --search "<term>"`, merged PRs that reference the issue number.
   - Record a per-deliverable verdict with evidence — `file:line`, commit hash, or PR number. An issue asking for deliverables {a,b,c} is implemented only if ALL landed.
   - Classify: status `implemented | partially-implemented | not-implemented | obsolete | superseded`; recommendation `close | close-as-superseded | update-scope | keep-as-is`.
   - Assess scope drift: renamed paths, relocated files, architectural decisions that moot the framing. Draft replacement scope text when recommending update-scope.
4. **Adversarially verify every audit** with an independent pass whose only job is to refute it. Bias: wrongly closing unfinished work is the costly error — downgrade doubtful closes. Prompt templates and output schema: `references/audit-verify-prompts.md`.

## Phase 2 — Decide (stop here)

Present a decision table (issue, verdict, recommended action) with per-issue rationale and evidence. Surface genuine judgment calls — keep-vs-descope, product-scoping questions, competing dispositions between auditors — as the owner's decisions; do not resolve them unilaterally. Include draft closing comments and replacement scope text so approval can be executed verbatim. Touch nothing until the owner approves.

## Phase 3 — Execute (after approval)

Order matters:

1. **Create new issues first** (consolidations, follow-ups) so their numbers can be cited in closing comments. Use the `file-issue` skill when available. Match project placement to sibling issues, and attach children to their epic as native sub-issues.
2. **Close with the correct reason**: `completed` for shipped work — including shipped-at-reduced-scope; `not planned` for superseded, descoped, or obsolete. Every close gets a terse rationale comment citing the landing commits/PRs and naming where any residual scope moved.
3. **Housekeep the epic**: rewrite the body — check off shipped items, restructure the remaining checklist around the new issue numbers, record scoping decisions up front — then post a short thread comment summarizing the reconcile (body edits do not notify watchers).
4. **Sync sub-issues**: every surviving child and every newly created issue must be natively attached to the epic (`references/gh-mechanics.md`), not merely listed in the body checklist.
5. **Sanity check**: re-run the Phase 1 enumeration and report the final open set.

## Conventions

- Write comment and body text to files and pass `--comment "$(cat file)"` / `--body-file` — inline backticks in double-quoted shell arguments get command-substituted.
- Comments stay terse and evidence-cited. No AI attribution anywhere.
- Phases 1–2 are strictly read-only: no closing, commenting, labeling, or editing during the audit.
