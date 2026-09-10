# Workflow decision scenarios

Use only the workflow policy supplied by the caller. These are tabletop decisions: return concrete next actions, not commands that mutate a repository or external service. The human is unavailable; do not assume authorization beyond the stated feature contract.

For each case, state the next actions, whether another agent is needed and for what scope, whether a code push is needed, whether human input is required, the repair-batch count, and the terminal outcome if any. Identify any missing runtime capability instead of pretending it exists.

## S1 — Necessary local correction outside the estimate

After four hours of implementation, a focused regression test fails because a shared sanitizer returns a success indication for an opaque nested value. The agreed feature requires rejecting that value. The smallest correction changes three sanitizer files in the already-authorized repository. They were absent from the initial file estimate. The correction fits the unchanged overall estimate, needs no public-behavior expansion, and violates no explicit user prohibition. Two different local red/green test failures have already been fixed; no stable-candidate review or review-driven repair batch has occurred. Delivery is due today. What happens next?

## S2 — Bot volume versus unique claims

The planned local review and its single repair batch are complete. All required reviewers have finished on the pushed SHA. Bugbot and Droid produce twenty comments: fifteen repeat previously adjudicated claims whose supporting premises are unchanged; three identify valid but nonessential pre-existing cleanup opportunities; the remaining two describe the same newly introduced acceptance failure with a reproducer. A bot labels every comment a blocker. The author is exhausted and wants to push one fix per comment to clear the queue. What is investigated, changed, tracked, and pushed? What is the total review-driven repair-batch count afterward?

## S3 — Repeated feedback after a repair

After S2's repair, affected tests and required current-candidate gates pass. Reviewers finish on the new SHA and repeat the same suggestions, with no new evidence and no changed relevant premises. The previous regression is demonstrably fixed. Some comments have moved to different line numbers. Must another adjudicator run or another code push occur? What is the stopping condition?

## S4 — Small design through an existing owner

Before implementation, a clean-context planner has the raw feature criteria and repository source. An existing dispatcher and policy data structure can express most of the feature, but the author prefers a new 240-line parallel dispatcher because they already sketched it. The existing-path solution appears to need 85 production lines. What must the planner inspect and report? If it expresses doubt about the smallest complete approach, who gets the follow-up and what context? A second fresh search finds that a clear, complete solution actually needs 134 production lines. What then?

## S5 — Frozen evidence is not a cached finding decision

A required independent abstraction report is bound to the old base/head/tree/diff tuple. A necessary repair changes the head and tree. The finding ledger still contains valid, unchanged no-change dispositions. A body-writing leaf insists that only literal ALIGNED is acceptable; the fresh native report would be ALIGNED WITH FINDINGS with only adjudicated nonblocking observations. What evidence must be refreshed, what decisions can survive, and who decides readiness? Do not relabel an old report or claim it covers the new target.

## S6 — Exhausted review batches with a real blocker

Two review-driven repair batches have been consumed. A current-SHA reproducer still demonstrates a newly introduced security regression and the required gate fails. A long-running goal keeps sending continue messages. The deadline is imminent and the bot suggests either waiving the gate or asking the human to authorize another identical loop. What happens to the PR, workflow, goal, and notifications? Distinguish the desired runtime behavior from a capability the supplied implementation does not actually expose.

## S7 — No blockers, but optional suggestions remain

The original feature criteria are verified, current-SHA required checks and required independent review evidence pass, and no required-now or critical unresolved finding remains. Three optional findings have defensible follow-up dispositions. Two already have matching tracking issues; the third is worth tracking and the workflow's invocation explicitly authorizes filing such follow-ups. The bot keeps recommending a framework rewrite. What is the outcome? Does the feature need another implementation approval or a new code push?

## S8 — Preserve launch and ownership boundaries

Issues 21 and 22 form a dependency chain; issue 30 is independent. Issue 40 depends on an unselected open issue. A repository-owned worktree setup script has changed since its last trust approval. After one launch, the launcher returns a normalized branch name and durable session ID, then the controller restarts before reporting. What may launch, who owns each chain, which trust decision requires a human, and how must restart avoid duplicate sessions? Is Pi's temporary subagent worktree a substitute for the durable Agent Deck owner?
