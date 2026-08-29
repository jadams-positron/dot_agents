---
name: distill
description: Simplify code or prose through one proportionate verified pass by default, with up to three passes while concrete safe reductions remain. Use for explicit requests to distill, simplify, tighten, shorten, or remove redundancy without losing substance.
---

# Distill

Produce the simplest complete form. Remove excess while preserving essential meaning, behavior, and intent.

> "I have made this letter longer than usual, only because I have not had the time to make it shorter." — Blaise Pascal

## Honor the Priority Order

Resolve conflicts in this order:

1. Preserve correctness and factual fidelity.
2. Preserve required behavior, meaning, constraints, evidence, intent, and voice.
3. Improve clarity for the intended reader.
4. Simplify structure and relationships.
5. Reduce words, lines, elements, and surface area.

Let shorter lose whenever it conflicts with correct, complete, or clear. Permit a local addition—a better name, guard clause, example, or explanation—when it reduces global complexity.

## Establish the Preservation Contract

Before editing:

1. Identify the artifact, purpose, audience, requested output, and applicable local conventions.
2. Extract the elements that must survive:
   - For code: observable behavior, public APIs, data and wire formats, error semantics, security properties, concurrency behavior, performance requirements, and tests.
   - For prose: claims, evidence, decisions, requirements, commands, names, dates, ownership, unresolved questions, tone, and requested structure.
3. Distinguish essential complexity from accidental complexity. Preserve necessary distinctions; target repetition, indirection, obscurity, and ceremony.
4. Inspect enough surrounding context to avoid making a locally concise change that increases system-wide confusion.
5. Do not invent missing facts or silently resolve ambiguity. Preserve or surface uncertainty.

## Use Proportionate Passes

Perform one `inspect -> edit -> verify` pass by default. Continue only for concrete material reductions and stop after three passes unless explicitly extended.

### Pass 1: Distill Substance and Structure

- Remove dead, irrelevant, repeated, stale, and speculative material.
- Organize around the primary purpose, decision, action, or execution path.
- Merge duplicated ideas and separate unrelated concerns.
- Prefer the smallest structure that makes the whole artifact easy to navigate.
- Preserve required context even when it is not brief.

Verify the result against the preservation contract and original artifact.

### Pass 2: Simplify Relationships and Expression

- Reduce nesting, indirection, coupling, unnecessary abstraction, jargon, hedging, and ornamental phrasing.
- Make control flow, ownership, causality, and dependencies obvious.
- Strengthen names, verbs, interfaces, topic sentences, and transitions.
- Replace explanation with clearer structure where possible.
- Avoid clever compression that transfers work from the author to the reader.

Verify meaning or behavior again. For code, run the narrowest useful formatter and tests after the pass.

### Pass 3: Compress and Challenge

- Make every remaining word, line, branch, parameter, comment, section, and dependency justify itself.
- Delete residue, combine equivalent statements, and shorten indirect constructions.
- Remove comments that only restate clear code; retain comments that carry contracts, rationale, constraints, or warnings.
- Prefer information density over blunt truncation.
- Compare the final artifact with both the original and the preservation contract.

Run proportionate verification. Stop unless another material reduction is concrete and the three-pass cap remains.

## Apply Artifact-Specific Rules

### Code

- Improve readability, maintainability, local reasoning, and ease of change rather than minimizing lines.
- Make small, behavior-preserving changes and verify between material steps.
- Prefer explicit, direct control flow over speculative frameworks or premature abstractions.
- Remove duplication only when the resulting abstraction is easier to understand and change.
- Preserve required documentation, generated-file boundaries, compatibility, and repository conventions.
- Run relevant formatters, tests, linters, and static checks. Do not claim preservation without evidence.

When the artifact contains Go, read [references/go.md](references/go.md) before editing it.

### Prose and Documentation

- Lead with the outcome, decision, request, or main claim.
- Use concrete subjects and verbs. Prefer familiar words without weakening technical precision.
- Keep one purpose per section and one main idea per paragraph.
- Remove throat-clearing, greetings, repeated summaries, stale history, and meta-commentary unless they serve the audience.
- Preserve citations, qualifications, counterexamples, exact commands, and unresolved questions that affect interpretation or action.

When creating or updating internal documentation, read
[references/documentation.md](references/documentation.md). For any runbook,
also read [references/runbooks.md](references/runbooks.md).

### Comments

- Explain why, the caller-visible contract, a non-obvious constraint, or a dangerous edge case.
- Improve the code before adding prose that narrates what unclear code does.
- Keep required API documentation even when the declaration appears self-explanatory.
- Delete obsolete, contradicted, or redundant comments.

### Notes, Messages, and Email

- Put the requested action, decision, or result first.
- Retain only the context needed to interpret or act.
- Make owner, deadline, dependency, and open question explicit when present.
- Preserve necessary interpersonal tone; do not make direct communication needlessly cold.

## Stop Deliberately

Stop when another deletion would reduce correctness, necessary context, clarity, usability, or maintainability. Do not chase a word-count or line-count target unless the user supplied one.

Return the final artifact in the requested form. Do not narrate the three passes unless the user asks. Briefly report verification, unresolved ambiguity, or a material preservation risk when one exists.
