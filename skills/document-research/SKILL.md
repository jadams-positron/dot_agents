---
name: document-research
description: This skill should be used when the user wants to create or update a research document in the Positron "Reliability & Orchestration Research" Notion database — capturing an investigation, evaluation, design exploration, spike, benchmark, or survey as a well-structured, well-cited database row. Triggers include "document this research", "write this up as a research doc", "add a research doc for X", "update the research doc on Y", or "log this investigation in Notion". Not for MEPs (those stay in Working Docs).
---

# Document Research

## Overview

Capture a research effort as a row in the Orchestration teamspace's **Reliability & Orchestration Research** Notion database, following that database's schema and the teamspace's documentation conventions. Two modes: **create** a new research row, or **update** an existing one (add findings, bump review date, conclude it).

This skill documents *already-performed* research; it does not perform the research. The input is findings the user (or a prior investigation) already produced. The job is to render them into a properly-structured, properly-propertied, well-cited Notion row.

## When to use

Trigger on requests like:

- "Document this research / write this up as a research doc"
- "Add a research doc for <question>"
- "Update the research doc on <topic>" / "mark that research concluded"
- "Log this investigation in the Research database"

Do **not** use this skill for MEPs (Model Enhancement Proposals) — by team ruling those live in Working Docs, not Research. Do not use it to *do* the research (fan-out investigation is separate work); use it once findings exist.

## Required reading before acting

1. `references/research-database.md` — the database IDs, full property schema, property-setting cheatsheet, and the teamspace conventions (question-first titles, no numbered sections, Concluded requirements, the index-row rule).
2. `references/citations.md` — **mandatory** citation discipline: exact permalink recipes for commit-pinned GitHub source links, PRs/issues, and Slack messages, plus the stale-working-tree line-number trap. Every research doc must cite its sources this way.
3. `references/notion-markdown.md` — the Notion-flavored-Markdown gotchas that matter for a research doc (tables as XML, escaping, callouts/columns/code blocks, dates, user mentions).
4. The **live** Notion spec resource `notion://docs/enhanced-markdown-spec` (read it via the MCP resource interface, not a URL fetcher). The cheatsheet is a summary; the live spec is authoritative and can change.

## Workflow

### 1. Determine mode and gather inputs

Decide **create** vs **update**:

- **Update** when the user references an existing doc (a Notion URL, or "the FPGA-fit research", "that investigation"). If given a URL, use it. Otherwise locate it with `notion-search` scoped to the data source (see `references/research-database.md`), and confirm the match with the user if ambiguous.
- **Create** otherwise.

Collect the properties the schema needs (see the reference for the full list and allowed values): a question-first **title**, **Type**, **Area**(s), **Status**, the **Question**, and — if the research is finished — a **TL;DR** and an outcome link for **Tracking**. Infer sensible defaults from the findings rather than interrogating the user; ask only for what cannot be inferred.

### 2. Fetch the database first (always)

Before writing, `fetch` the database to confirm the current data source ID and schema — this self-heals if IDs or options drift from the reference. Note the `data_source_id` (a `collection://…` URL) for the parent.

### 3. Look up people

If setting **Owner**, resolve the person to a Notion user ID with `notion-get-users` (query by name/email). Person properties take a JSON array of user IDs.

### 4. Write the body

Read the live enhanced-markdown spec, then compose the body in Notion-flavored Markdown. Follow the recommended research-doc skeleton in `references/research-database.md`. Non-negotiables:

- **Cite every load-bearing claim — non-negotiable.** Every quantitative claim, quoted statement, and "the code does X" assertion needs a specific, clickable source: a **commit-pinned** GitHub file+line permalink, a PR/issue/commit link, or a real Slack message permalink. Follow `references/citations.md` exactly — including its warning that a stale local clone yields wrong line numbers, so verify each line at the pinned commit (`git grep -n <anchor> <sha> -- <path>`). Bare `file:line` strings, `#channel` names, or "per Slack" do not count. Inline or a bottom "Key source references" section (or both) is fine; absent is not.
- **No numbered section scheme** (teamspace rule). Use descriptive `##` headers, never a "05/10/20/30" or "1./2./3." section numbering.
- **Do not add arbitrary blank lines — no `<empty-block/>` padding.** Notion already renders correct spacing between blocks; inserting `<empty-block/>` before/after headers, around tables, or between paragraphs produces visibly bloated pages. Write blocks back to back. Reserve `<empty-block/>` for the rare case where a genuinely empty visual line is the intent, not as separator hygiene.
- Lead with a bottom-line callout / TL;DR so a skimming reader gets the answer immediately.
- Use the `<table>` XML form for tables (Notion Markdown does not take pipe tables); wrap anything with `` ` `` / `[` / `<` / `$` etc. in code spans, or escape it, outside code blocks.

### 5. Create or update

- **Create:** `notion-create-pages` with a `data_source_id` parent (from step 2). Set all properties in the same call. Use expanded date property names (`date:Started:start`, etc.) — see the reference. Give the page a fitting emoji `icon`.
- **Update:** `fetch` the page first to read its current body and properties, merge the new material in (don't clobber unrelated content), then `notion-update-page`. Always bump **Last Reviewed** to today. When concluding, set **Status = Concluded** and ensure **TL;DR** and **Tracking** are present (the database expects both on a concluded row).

### 6. Verify

`fetch` the page after writing and confirm the properties resolved (Owner mention, Area, dates, Status) and the body rendered (callouts, tables, code blocks did not break). Report the page URL to the user.

## Notes and boundaries

- **Teamspace-parent limitation:** the Notion API cannot create pages at the teamspace top level. Creating a **row under the data source** (as this skill does) is the correct, working path — no human drag needed. Only free-standing teamspace pages hit that limitation.
- **Index-row rule:** a research effort that is primarily tracked in another database (Intake, SSI Follow-up, Known Issues) gets a lightweight *index row* in Research that links out — it is never moved out of its home tracker.
- **Relations:** `Resulted in ADR` and `Known Issue` are two-way relations to other databases (IDs in the reference). Populate them when the research produced an ADR or maps to a known issue; otherwise leave empty.
- **Deploying this skill:** the dot_agents repo syncs to agent dirs via `gaal sync`, which resets the repo to `origin/main` and drops uncommitted work — commit and push skill changes first, and add the skill's `name` to the gaal config `select` list, before syncing.
