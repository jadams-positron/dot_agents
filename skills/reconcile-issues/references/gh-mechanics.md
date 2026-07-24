# GitHub mechanics for issue reconciliation

All commands use the `gh` CLI. Substitute `<o/r>` with `owner/repo`.

## Enumerating an issue set

```bash
gh issue list --repo <o/r> --state open --search "houston in:title" \
  --json number,title,labels,assignees --limit 200
gh issue list --repo <o/r> --state open --label some-label --json number,title
```

`in:title` search also matches partial words — review the hits, don't trust the filter blindly.

## Native sub-issues (epics)

Sub-issues are first-class in GitHub (progress bar on the parent, "parent" link on the child). A markdown checklist in the epic body is NOT a sub-issue relationship — always sync the real thing.

```bash
# list a parent's sub-issues
gh api repos/<o/r>/issues/<parent>/sub_issues --jq '.[].number'

# attach a child (needs the child's numeric database id, not the node ID)
id=$(gh api repos/<o/r>/issues/<child> --jq .id)
gh api -X POST repos/<o/r>/issues/<parent>/sub_issues -F sub_issue_id=$id

# detach
gh api -X DELETE repos/<o/r>/issues/<parent>/sub_issue -F sub_issue_id=$id
```

Notes: `gh api ... --jq .id` on the REST issue endpoint returns the numeric database id (correct); `gh issue view --json id` returns the GraphQL node ID (wrong for this API). `-F` coerces numeric strings to JSON numbers. Closed issues can be (and should stay) attached — they drive the parent's progress bar.

## Close reasons

| Situation | `--reason` |
|---|---|
| All deliverables landed | `completed` |
| Landed at reduced scope, remainder declared non-goals | `completed` (comment lists the dropped non-goals) |
| Need met a different way / premise vanished / descoped | `not planned` |
| Residual scope consolidated elsewhere | match the shipped half: `completed` if the core landed, else `not planned`; comment links the new issue |

## Closing with a rationale comment

Write the comment to a file first — inline backticks in a double-quoted shell argument get command-substituted:

```bash
gh issue close <n> --repo <o/r> --reason "not planned" --comment "$(cat c<n>.txt)"
```

A good closing comment: 1–4 sentences; cites landing commits/PRs by hash/number; names where residual scope moved; states the scoping decision if one was made. No AI attribution.

## Hunting evidence

```bash
git fetch origin <default-branch>
git log origin/<branch> --oneline -i --grep='<term>'          # landing commits
git show origin/<branch>:<path>                               # file content at ground truth
gh pr list --repo <o/r> --state all --search '<term>' --json number,title,state,url
gh pr list --repo <o/r> --state merged --search '"#<issue>"'  # PRs referencing the issue
gh issue view <n> --repo <o/r> --comments                     # full thread
```

Cross-check both directions: code that exists without the issue's naming (absorbed into another package), and cited evidence that does not exist (auditor hallucination).

## Project membership

New issues should match their siblings' project placement:

```bash
gh issue view <sibling> --repo <o/r> --json projectItems --jq '[.projectItems[].title]'
```

## Epic body edits

```bash
gh issue edit <epic> --repo <o/r> --body-file new-body.md
gh issue comment <epic> --repo <o/r> --body "…reconcile summary…"   # body edits don't notify
```
