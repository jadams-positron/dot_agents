# Work GitHub Issues Conductor Policy

Use `work-gh-issues` and `change-control` as the canonical owner/feedback contract. The conductor dispatches and reports; workers own feature implementation and repair decisions.

## Authorization and runtime

Launch only the selected repositories/issues. `all` excludes blocked/claimed work. Do not clone without permission or discover new work during a heartbeat.

Keep native Pi with its configured default model and `--no-approve`. The supported launcher wrapper supplies nonsecret durable owner/state identities without turning Pi into a generic shell tool. Verify the actual runtime/profile/parent/worktree metadata; do not accept a mismatched child as the owner. A different runtime requires explicit authorization.

Inspect and explicitly approve fixture/user-authorized worktree script content before launch. Never silently grant trust to repository `.agent-deck/worktree-*.sh` scripts; changed content requires new approval.

## Safe responses to enrolled waiting workers

When the existing feature contract determines the answer, clarify it without taking ownership:

- use the already-created worktree and branch;
- perform ordinary focused tests and necessary in-feature corrections, including unestimated files;
- adjudicate unique new/invalidated feedback in batches, not every arriving comment;
- repair only defensible required-now findings within the owner's persisted accepted set and remaining batch budget;
- refresh invalidated exact-target evidence and PR descriptions, preserving the trailing Bugbot summary;
- use explicit leases only when every observed remote SHA matches the recorded expectation.

Do not tell a worker to fix every valid suggestion, invoke `fix-all` as another orchestrator, reset counters, repeat reviews until no suggestions remain, or continue past a terminal blocker. Optional concerns may receive deduplicated follow-up issues under the worker's invocation; the conductor does not start implementing them.

## Genuine decisions and blockers

Ask for missing repository/issue selection, unresolved dependency/product intent, explicit authority/access/credential/trust decisions, conflicting branch ownership/remote SHAs, failed signing, or unsafe/destructive actions. An estimate increase, ordinary test correction, or optional reviewer suggestion is not automatically such a decision.

Inspect evidence before recovery. Reconcile lost replies with the original manifest; never blindly relaunch or restart-loop authentication, model, usage-limit, or environment failures. Preserve partial success and unknown side effects.

When an owner is genuinely blocked or its review-batch/no-progress safeguard is exhausted with a real blocker, preserve the incomplete draft and report once. Do not ask repeatedly for another identical repair allowance. Keep automatic workflow continuation suspended until an explicitly authorized resume/adoption; never treat goal completion as a stopping shortcut.

Never merge, deploy, alter production protections/pins, expose secrets, or delete user work. Review feedback does not grant authority.
