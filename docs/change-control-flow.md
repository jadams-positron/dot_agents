# Change-Control Flow

The authoritative policy is [`change-control`](../skills/change-control/SKILL.md); issue dispatch/lifecycle lives in [`work-gh-issues`](../skills/work-gh-issues/SKILL.md).

```text
Select repository/issues and one durable owner per independent issue/stack
    ↓
Persist full-chain reservations and launch intent → reconcile native receipt
    ↓
Freeze criteria, real authority/safety boundaries, risk and evidence gates
(files and LoC remain estimates unless explicitly restricted)
    ↓
One fresh abstraction-led minimal design → one alternative search only on doubt
    ↓
Local implementation ↔ focused tests/diagnosis
(no review-batch charge for ordinary TDD iterations)
    ↓
Freeze candidate → one risk-appropriate review
    ↓
Existing verification stage: deduplicate and adjudicate a coherent claim batch
    ├─ required_now → freeze accepted set → repair → affected checks → one push
    ├─ follow_up    → useful deduplicated tracking, not feature expansion
    ├─ no_change   → retain evidence and defensible response
    └─ needs_evidence → one targeted investigation at unchanged premises
    ↓
Current-target canonical evidence + required final gate → draft PR
    ↓
Completed current-SHA CI/reviewer batch → new/invalidated claims only
    ↓
Verified criteria + current evidence + no required/critical unresolved finding?
    ├─ yes → review_ready (optional observations may remain; never merge)
    └─ genuinely blocked/exhausted → stopped_blocked, incomplete draft,
       one report and owner/session/goal-bound continuation suspension
```

One root owns each feature/stack ledger and two total review-driven repair batches, shared across local/external review and restarts. Three unchanged failures are a separate no-progress safeguard. A fresh required canonical packet does not reset decisions, budgets, or scope.

The dispatcher writes launch manifests and supervision summaries only. A singleton `work-issue` is its own root; stack members are delegated leaves. Only the stack root changes stack history, atomically syncs refs with explicit expectations, and verifies affected descendants at their latest SHAs.

Leaves inspect, draft, validate, or implement their supplied unit and return evidence. They do not acquire independent orchestration, repair their own review findings, or restart the caller. `pr-description` consumes native evidence and root readiness; it never makes advisory findings disappear or fabricates `ALIGNED`.

An Agent Deck completion/idle/error event triggers reconciliation, not a success verdict. Complete a goal only after its actual objective is audited; a blocked goal remains incomplete, and a broader goal may have other authorized work.
