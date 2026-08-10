# Work GitHub Issues Conductor Policy

These rules refine Agent Deck's shared conductor policy for GitHub issue work.

## Launch Authorization

- Launch only repositories and issues explicitly authorized by the user.
- `all` means all issues currently classified as available in the named
  repository. It never includes blocked or in-progress issues.
- Do not clone a missing repository without explicit permission.
- Do not discover or launch new work during a heartbeat.

## Model Selection

- Keep the `work-gh-issues` default on Codex `gpt-5.6-sol`.
- If the user separately authorizes a Claude worker or verifier, require
  `claude-opus-5`; never launch or accept work from `claude-fable-5`.
- Verify the live session model after launch. Stop a mismatched child before
  accepting its result, then replace it through its owning conductor.

## Safe Worker Responses

Auto-respond when the worker is waiting and the existing contract determines
the answer:

- continue through required tests, local review, `fix-all`, CI, and Bugbot;
- use the Agent Deck-created worktree and branch;
- fix every validated finding and rerun affected checks;
- refresh PR descriptions and evidence against the final SHA, preserving any
  Bugbot summary appended to the live body byte-for-byte at the end;
- use `--force-with-lease` only for a solely owned issue or stack branch when
  the observed remote SHA matches the worker's recorded expectation.

## Always Escalate

- repository selection, issue selection, or permission to clone;
- dependency cycles, branching stacks, ambiguous ordering, or an unselected
  prerequisite;
- product behavior, scope, architecture, or compatibility decisions not
  settled by the issue or repository;
- secrets, credentials, production access, deployment, or merge requests;
- plain `--force`, protected/default branch mutation, deletion, or destructive
  database/infrastructure actions;
- an unexpected branch owner or remote SHA, failed signing, or evidence that
  another checkout moved a stack branch;
- repeated CI, authentication, model, or environment failures without a proven
  safe recovery.

## Failure Handling

- Inspect an error's substate and output before restarting a child. Never
  restart-loop authentication, usage-limit, or model failures.
- If Agent Deck refuses an untrusted repository worktree script, show the exact
  script path and ask the user to inspect and approve it with
  `agent-deck worktree trust-scripts <repo-path>`. Never grant trust yourself.
- Keep partial successes in the batch manifest. Report failed owners and do not
  relaunch them without authorization.

Never merge, deploy, expose secrets, or add AI attribution.
