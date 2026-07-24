# GitHub Projects at positron-ai

Positron's GitHub Projects (v2) are owned at the **org level** (`positron-ai`), not at the repo level. An issue in any repo under the org can be attached to any org-level project.

## Listing projects

```bash
gh project list --owner positron-ai
```

Output columns: `NUMBER`, `TITLE`, `STATE`, `ID`. The `NUMBER` is what `gh project item-add` and `gh project item-list` take.

## Common projects

The current default for new tickets is **MCC**:

| User says | Title in `gh project list` | Number |
|-----------|----------------------------|--------|
| "MCC" / "Mission Control Center" / "Orchestrator" | `Mission Control Center` (renamed from `Misson Control Center (a.k.a. Orchestrator)`) | 31 |

Project numbers and titles change over time. Always confirm by running `gh project list --owner positron-ai` rather than trusting the table above. If the lookup returns a different number, update this table.

## Adding an existing issue to a project

```bash
gh project item-add <project-number> \
  --owner positron-ai \
  --url https://github.com/positron-ai/<repo>/issues/<n>
```

## Listing items already in a project

```bash
gh project item-list <project-number> --owner positron-ai --limit 50
```

## Common pitfalls

- **`--owner` is required** — without it, `gh` defaults to the user's projects, not the org's.
- **Use the number, not the ID** — `gh project list` shows both; `item-add` wants the integer number.
- **`project` scope on the token** — `gh auth status` must list `read:project` or `project`. If not, run `gh auth refresh -s project` (interactive).
- **Titles drift** — the MCC project was renamed at least once (`Misson` → `Mission`). Match loosely when grepping the listing, then use the number.

## Sibling placement heuristic

When the new issue relates to existing issues (follow-up, epic subtask, consolidation), match their project placement instead of guessing:

```bash
gh issue view <related-issue> --repo positron-ai/<repo> \
  --json projectItems --jq '[.projectItems[].title]'
```

Children of an epic that is itself in a project belong in that project, even when other siblings were filed without one.
