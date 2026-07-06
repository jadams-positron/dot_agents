---
name: documentation-distiller
description: Distill messy, verbose, incomplete, or draft internal documentation into concise, structured, actionable docs. Use when cleaning setup docs, requirements notes, planning pages, wikis, runbooks, dependency lists, operational procedures, audits, decision records, or implementation briefs while preserving technical facts, gaps, constraints, and decisions.
---

# Documentation Distiller

Convert rough internal documentation into concise, structured, implementation-ready output. Preserve facts, requirements, constraints, commands, decisions, and open questions. Remove text that does not help a reader act.

## Workflow

1. Identify the document's purpose: requirements, runbook, setup guide, audit, decision record, checklist, or implementation brief.
2. Extract durable content: required state, commands, dependencies, owners, constraints, inputs, outputs, risks, verification steps, and unresolved questions.
3. Separate confirmed facts from assumptions and missing information.
4. Choose the smallest useful structure for the document type.
5. Rewrite densely. Keep only content that affects action, implementation, operation, or review.

## Distillation Rules

- Remove greetings, filler, repeated context, stale history, and conversational phrasing.
- Preserve exact commands, package names, versions, paths, URLs, config keys, service names, error strings, and acceptance criteria.
- Do not invent missing commands, versions, owners, credentials, URLs, or implementation details.
- Convert prose instructions into checklists, tables, command blocks, or requirement bullets where useful.
- Keep rationale only when it explains a constraint, tradeoff, or decision.
- Flag missing or ambiguous inputs explicitly.
- Use synthetic placeholders for credentials, users, hosts, tokens, and private values.
- Prefer reusable structure over one-off formatting.

## Output Selection

Choose the output shape based on the source and user request:

- **Requirements brief**: goal, required capabilities, constraints, open decisions, acceptance criteria.
- **Setup guide**: target environment, prerequisites, install steps, configuration, verification.
- **Runbook**: trigger, impact, procedure, validation, rollback, escalation.
- **Audit summary**: findings, evidence, risks, required fixes, unknowns.
- **Decision record**: decision, context, options considered, consequences, follow-up.

Use a requested format when the user provides one.

## Default Output Template

## Purpose

- One sentence describing what this document is for.

## Required Facts

- Confirmed technical facts, dependencies, commands, constraints, or decisions.

## Procedure Or Requirements

- Actionable steps or requirements, grouped in execution or review order.

## Verification

- Checks that prove the expected state or outcome.

## Open Questions

- Missing inputs, ambiguous requirements, unclear ownership, or unresolved decisions.
