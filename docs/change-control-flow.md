# Change-Control Flow

This is the control flow shared by scope-aware coding workflows. The canonical policy is [`change-control`](../skills/change-control/SKILL.md).

File lists, diff estimates, and repair/retry counts are planning information, not approval gates. Continue necessary in-scope implementation and verification as estimates change. Honor explicit user limits and stop for genuine blockers, missing authorization, or safety concerns—not agent-invented size or attempt caps.

```text
USER REQUEST
    |
    v
+--------------------------------------+
| Select exactly one root orchestrator |
|                                      |
| standalone issue   -> work-issue     |
| issue stack        -> work-gh-issues |
| explicit long run  -> wiggum         |
| broad refactor     -> refactor-campaign
+--------------------------------------+
    |
    v
+----------------------------------+
| Establish scope and safety       |
|                                  |
| - acceptance criteria            |
| - safety invariants              |
| - base and candidate head        |
| - advisory file/diff estimates   |
| - generated artifacts            |
| - risk tier and required gates   |
| - explicit user limits only      |
+----------------------------------+
    |
    v
+-------------+     +----------------+     +------------------+
| LOW RISK    |     | MEDIUM RISK    |     | HIGH RISK        |
| focused     |     | proving test   |     | complete gate    |
| checks; no  |     | and one        |     | and one combined |
| reviewer by |     | focused review |     | multi-angle review
| default     |     |                |     |                  |
+------+------+     +-------+--------+     +---------+--------+
       |                    |                        |
       +--------------------+------------------------+
                            |
                            v
                 +------------------------+
                 | Implement the smallest |
                 | correct diff           |
                 |                        |
                 | - frozen scope only    |
                 | - focused checks       |
                 | - track diff growth    |
                 +-----------+------------+
                             |
                             v
                 +------------------------+
                 | Classify each finding  |
                 +------------------------+
                   |       |       |      |
                   v       v       v      v
                BLOCKING COUPLED UNRELATED UNCERTAIN
                   |       |       |      |
                   |       |       |      +--> STOP AND ASK
                   |       |       +---------> REPORT ONLY
                   +---+---+
                       |
                       v
          authorized in-scope work?
                    /      \
                  yes      no
                   |        |
                   v        +--------------> STOP AND ASK
                 repair
                   |
                   v
          update estimates and explain
          actual changed surface
                   |
          new authorization needed?
                 /      \
               no       yes
               |         |
               v         +----------------> STOP AND ASK
     +-------------------------+
     | Freeze stable candidate |
     | exact base/head/diff     |
     +------------+------------+
                  |
                  v
     +-------------------------+
     | One risk-appropriate    |
     | review                  |
     +------------+------------+
                  |
                  v
        validate and classify
             review findings
                  |
          blocking or coupled?
              /         \
            no          yes
            |            |
            |      genuine blocker?
            |         /       \
            |       no        yes
            |        |         |
            |        v         +----------> STOP AND ASK
            |    focused repair
            |    and invalidated
            |    checks only
            |        |
            +--------+
                  |
                  v
     +-------------------------+
     | Required final gate     |
     | once on final candidate |
     +------------+------------+
                  |
             gate passes?
              /       \
            yes       no
             |         |
             |    classify failure
             |    and repair in scope,
             |    or report a blocker
             |
             v
     +-------------------------+
     | pr-description leaf     |
     | consumes root evidence  |
     +------------+------------+
                  |
                  v
     +-------------------------+
     | Create draft PR         |
     | CI and Bugbot follow    |
     | the same scope rules    |
     +------------+------------+
                  |
                  v
     +-------------------------+
     | Final verification      |
     | - latest SHA green      |
     | - no blocking findings  |
     | - scope/limits recorded |
     +------------+------------+
                  |
                  v
     +-------------------------+
     | Mark ready and report   |
     | Never merge             |
     +-------------------------+
```

## Leaf-skill rule

```text
ROOT ORCHESTRATOR
    |
    +-- fess ---------------------- read once; return findings
    +-- abstraction-review -------- review frozen target; return evidence
    +-- fix-all ------------------- repair supplied finite set once
    +-- pr-description ------------ draft or validate once
    `-- differential harness ------ compare; return differences

Leaves never dispatch, invoke an orchestrator, broaden scope, own retries,
commit, push, repair their own findings, or restart the caller.
```

## Stack flow

```text
work-gh-issues  [SOLE ROOT / STACK OWNER]
    |
    +-- record stack/per-issue criteria and explicit user limits
    +-- issue A -> delegated work-issue -> focused checks -> commit A
    +-- issue B -> delegated work-issue -> focused checks -> commit B
    +-- issue C -> delegated work-issue -> focused checks -> commit C
    +-- rebase stack
    +-- freeze aggregate candidate
    +-- one aggregate risk-appropriate review
    +-- in-scope repairs routed to the owning issue
    +-- one final stack gate
    +-- pr-description leaf per immediate PR diff
    +-- submit stack
    +-- in-scope CI/Bugbot handling bottom-to-tip
    +-- mark ready when every latest SHA is green
    `-- never merge
```
