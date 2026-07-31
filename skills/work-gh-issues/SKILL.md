---
name: work-gh-issues
description: Fan out one or more GitHub issues into independent Agent Deck Codex sessions, each with its own worktree and branch and a shared end-to-end work-issue prompt. Use when the user asks to batch, start, launch, work, or orchestrate GitHub issues through Agent Deck, especially positron-ai/capcom issues, or invokes /work-gh-issues. If no issue numbers are supplied, ask the human for them before launching anything.
---

# Work GitHub Issues

Launch one Agent Deck worker per GitHub issue with fixed isolation, model, group,
and quality-gate settings.

## Collect issue numbers

1. Extract positive issue numbers from the user's request. Accept `21`, `#21`,
   whitespace-separated values, or comma-separated values.
2. If none are present, ask: `Which GitHub issue numbers should I launch? You
   can provide a space- or comma-separated list.` Then stop and wait for the
   human's response. Do not infer numbers or enumerate open issues.
3. Treat the human's response as a continuation of the same invocation.

## Launch workers

Run the bundled launcher rather than reconstructing `agent-deck launch`
commands:

```bash
python3 <skill-dir>/scripts/launch.py <issue> [<issue> ...]
```

Defaults:

- Repository: `$CAPCOM_REPO`, otherwise `~/code/github/positron-ai/capcom`
- Agent Deck group: `capcom`
- Session title, branch, and worktree leaf: `work#<issue>`
- Worktree location: `<repo>/.worktrees/work#<issue>`
- Agent and model: Codex `gpt-5.6-sol`

Use `--repo PATH` only when the repository is elsewhere. Use `--dry-run` to
inspect generated commands without creating sessions or worktrees. Do not add
`--no-parent`: when invoked inside Agent Deck, parent linkage provides status
notifications without coupling worker execution.

The launcher validates all inputs before creating anything, de-duplicates issue
numbers, locks session titles, and continues launching later issues if one
Agent Deck command fails.

## Worker contract

Each worker receives instructions to:

1. Run `work-issue` end to end for its issue.
2. Reuse the Agent Deck-created worktree and branch; never create a nested
   worktree or rename the branch.
3. Before the first push or PR creation, perform a thorough local multi-angle
   review using `agent-pr-review` methodology, run `fix-all` on every validated
   finding, and rerun relevant tests until clean.
4. Create a draft PR assigned to `@me`, apply appropriate labels from the
   issue, include `Closes #<issue>`, complete the normal CI and Bugbot flow,
   never merge, and never add AI attribution.

`agent-pr-review` itself requires an existing remote PR and posts a pending
review, so the pre-push gate uses its methodology locally rather than claiming
to execute its GitHub-posting step.

## Report

Report every successfully launched issue and every failure. On success, tell
the human to open the scoped view with:

```bash
agent-deck -g capcom
```
