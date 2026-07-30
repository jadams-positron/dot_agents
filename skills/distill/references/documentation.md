# Internal Documentation

Use this guidance for setup docs, requirements, planning pages, wikis,
dependency docs, operational procedures, audits, decision records, and
implementation briefs. For a new document, treat the user's requirements and
verified source material as the preservation contract.

## Preserve Durable Information

- Preserve exact commands, package names, versions, paths, URLs, config keys,
  service names, error strings, acceptance criteria, warnings, and ordered
  dependencies.
- Capture required state, inputs, outputs, constraints, owners, risks,
  verification, and unresolved questions when they affect action or review.
- Separate confirmed facts from assumptions and missing information.
- Do not invent commands, versions, owners, credentials, URLs, or
  implementation details.
- Replace credentials, users, hosts, tokens, and other private values with
  clear synthetic placeholders.
- Keep rationale only when it explains a constraint, tradeoff, or decision.

## Choose the Smallest Useful Shape

- **Requirements brief:** goal, capabilities, constraints, open decisions,
  acceptance criteria.
- **Setup guide:** target environment, prerequisites, installation,
  configuration, verification.
- **Runbook:** trigger, impact, prerequisites, procedure, validation, rollback,
  escalation.
- **Audit summary:** findings, evidence, risks, required fixes, unknowns.
- **Decision record:** decision, context, options, consequences, follow-up.

Use the requested or repository-mandated format when one exists. Otherwise use
only the headings the content needs, selected from:

1. Purpose
2. Required facts
3. Procedure or requirements
4. Verification
5. Open questions

Prefer a checklist, table, or command block when it makes execution or review
faster. Do not impose a template that adds empty or ceremonial sections.
