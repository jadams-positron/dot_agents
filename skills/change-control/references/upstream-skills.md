# Consuming upstream skills

Superpowers is **consume-only** from `coctostan/pi-superpowers`. Do not patch, fork for workflow changes, or replace its distribution to implement this contract. Record the upstream revision used for qualification; update it only through the normal upstream-consumption process.

This caller contract does not add a mode to an upstream skill. Under `work-issue`/`work-gh-issues`, the owned workflow defines execution, admission, and completion. Use upstream technical practices within those steps, not an upstream orchestration flow with conflicting checkpoints:

| Upstream guidance | Owned workflow behavior |
|---|---|
| `writing-plans` execution handoff | Record the plan and estimates; the existing root continues the already authorized execution. No second execution-choice checkpoint. |
| `executing-plans` batch “report and wait” or ordinary-failure stop | Report useful progress while continuing local diagnosis and focused tests. Return only at a delegated leaf's assigned boundary or a genuine blocker. |
| `receiving-code-review` implementation of correct suggestions | First apply the shared validity/necessity disposition contract. Only the frozen `required_now` set authorizes review-driven repairs. Correct optional preferences can remain `no_change`. |
| `finishing-a-development-branch` integration-choice handoff | Follow the root's authorized publication/outcome steps. Do not start another orchestrator, implicitly merge, or add a routine approval stop. |

This precedence applies only inside the explicitly selected owned workflow. Standalone upstream invocations retain their upstream behavior. It never overrides explicit user restrictions, repository-required gates, credentials, script trust, destructive-operation boundaries, or branch ownership.

Qualify fresh-context decisions against the **unchanged** upstream texts plus this caller contract. Modified upstream fixtures cannot establish compatibility. A contradictory upstream update requires correcting the owned integration or withholding rollout—not silently editing the consumed dependency.
