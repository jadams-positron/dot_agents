# Auditor and verifier prompt templates

Templates for the Phase 1 fan-out. With the Workflow tool, run as a pipeline — each issue's verifier starts as soon as its audit finishes (no barrier). With the Agent tool, launch auditors in parallel batches. Sequentially, apply the same prompts one issue at a time.

Both prompts must carry a shared context block: repo checkout path, the ground-truth ref (`origin/<default-branch>` at a named tip commit), where the relevant code lives, and the HARD RULES (read-only: no closing, commenting, labeling, editing, pushing).

## Audit output schema

```json
{
  "issue": 0,
  "status": "implemented | partially-implemented | not-implemented | obsolete | superseded",
  "recommendation": "close | close-as-superseded | update-scope | keep-as-is",
  "evidence": ["file:line / commit / PR# — short note", "..."],
  "scope_assessment": "how the world moved since filing; what sub-scope remains; what wording is stale",
  "proposed_action": "draft closing comment citing landing commits/PRs, OR replacement scope bullets verbatim"
}
```

## Auditor prompt skeleton

```
You are auditing GitHub issue #<n> ("<title>") in <o/r> to decide if it is already
implemented (closable), partially done, obsolete, or still valid with drifted scope.
<context block>
Steps:
1. gh issue view <n> --repo <o/r> --comments — read the FULL body and every comment.
   Extract the concrete deliverables (each verb, flag, file deletion, doc, CI job).
2. For EACH deliverable, hunt for it in the codebase and history: grep the tree, check
   files the issue says to delete, build recipes, CI workflows, docs. Use
   git log origin/<branch> -i --grep=<term> and gh pr list --state all --search to find
   landing PRs, including merged PRs that reference #<n>.
3. Decide per-deliverable: done / not done / no-longer-relevant, with evidence
   (file:line, commit hash, or PR#).
4. Judge scope drift: has the architecture evolved so the issue's framing is stale?
   If work remains, write the updated scope in 2-5 bullets an operator could act on.
Be skeptical of partial matches: an issue asking for {a,b,c} is 'implemented' only if
ALL exist on origin/<branch>. Recommendation semantics: close = fully done;
close-as-superseded = the need was met another way or vanished; update-scope = still
wanted but the body needs rewriting; keep-as-is = still accurate.
```

For an epic: focus on whether the body/checklist matches the actual child set and shipped surface; recommend close only if all children are effectively done, else update-scope with a corrected checklist. For an adjacent issue (same subsystem, different framing): audit each half of its scope separately.

## Verifier prompt skeleton

```
Adversarially verify this audit of issue #<n> in <o/r>. Your job is to REFUTE it.
<context block>
The audit under review: <audit JSON>
Attack from whichever angles apply:
- If it says close/implemented: re-read the issue and hunt for ANY deliverable the
  auditor glossed over — a missing verb, a file it said to delete that still exists on
  origin/<branch>, a doc or CI job never added. Spot-check cited evidence: do the
  files/commits/PRs exist and do what is claimed (git show, gh pr view)?
- If it says not-implemented/keep: search for code the auditor missed — different
  naming, a merged PR referencing #<n>, functionality absorbed into another package.
- If it says update-scope: is the rewritten scope grounded in the current
  architecture, or does it invent work nobody needs?
Closing an issue whose work is NOT fully landed is the costly error — when in doubt
about close, downgrade it. Return agrees=true only if status AND recommendation both
survive; otherwise the corrected pair plus a specific critique.
```

Verdict schema: `{ "agrees": bool, "corrected_status": ..., "corrected_recommendation": ..., "critique": "what the audit got wrong or missed" }`.

## Known auditor failure modes (feed these to verifiers)

- **Working-tree contamination**: auditor reads the checked-out feature branch and reports a consumer/file that no longer exists on the default branch. Demand `origin/<branch>`-pinned citations.
- **Deliverable glossing**: "implemented" based on the headline feature while a deletion/doc/CI acceptance criterion is unmet.
- **Evidence mislabeling**: citing an issue number as a PR, conflating commit subject with PR title, off-by-a-few line numbers. Harmless individually — but verify anything load-bearing.
- **Missed absorption**: functionality landed under different naming or in a different package; search by behavior, not just by the issue's vocabulary.
