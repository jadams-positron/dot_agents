# Worker and integration protocol

## Worktree topology

Resolve the absolute common directory with
`git rev-parse --path-format=absolute --git-common-dir`. For a normal
repository, use its parent as the primary repository directory; stop and choose
an explicit safe location for a bare or unusual layout. Place campaign
worktrees under the repository's existing worktree convention, or under
`<primary-repository>/.worktrees/` when none exists. Never create a worktree
inside the integration worktree.

Before creation, inspect `git worktree list --porcelain`, local branches, and
the proposed path. Reuse an existing path or branch only when the campaign state
proves ownership and its recorded SHA matches. Otherwise stop on the collision.

Create only DAG-ready units. Use the frozen baseline SHA for root units and the
recorded post-integration SHA for dependent units.

## Worker prompt

Include the unit manifest, exact worktree path, branch, starting SHA, repository
instructions, and relevant test commands. State this contract explicitly:

```text
You own this unit and worktree only. Other agents are working in sibling
worktrees; do not revert, clean, overwrite, or integrate their work. Do not
spawn subagents.

Implement exactly the manifest outcome. Inspect broadly but edit only owned or
permitted supporting files. If another file, unit, repository, or behavior
change is required, stop and report the dependency instead of expanding scope.

Follow repository TDD and safety rules. Add a test that fails for the missing
boundary before changing production code when the project requires TDD. Do not
delete, skip, weaken, or suppress tests or checks.

Run focused verification. Before committing, coordinate any serialized hook or
shared-cache gate with the orchestrator. Commit with required signing and hooks;
never bypass either. Do not push, open a PR, merge, rebase, remove a worktree,
or edit the integration branch.

Return the commit SHA, changed files, exact commands and results, remaining
uncertainty, and a clean-worktree status.
```

## Independent unit audit

Give a fresh read-only auditor the unit manifest, baseline/start SHA, worker
commit, diff, repository instructions, and raw test output. Ask it to apply the
`fess` standard to scope fidelity, stubs, vacuous tests, mock drift, error
swallowing, suppressions, fallback paths, documentation drift, loose ends, and
unverified claims. Require file-and-line evidence and explicit verification
actions for uncertainty.

Have the coordinator validate each report. Send real findings to the original
worker and require an amended commit plus repeated tests. Do not let an auditor
edit or integrate code.

## Pre-integration checklist

Verify all of the following before merging a unit:

- the integration worktree is clean and at the recorded SHA;
- the worker worktree is clean;
- the unit branch descends from its declared starting SHA;
- every commit belongs to the unit and has required signing;
- the diff stays within ownership and contains no hook or test weakening;
- focused tests passed on the final worker commit; and
- the independent audit has no unresolved real finding.

Integrate one unit at a time. Record pre-merge SHA, unit commit, merge SHA, tree
SHA, and post-merge verification. Never start a dependent unit until this record
is complete.

## Conflict and failure handling

Abort a conflicted integration before doing unrelated work. Return the unit to
its worker with the latest integration SHA and the dependency that caused the
conflict. Require it to resolve and retest inside its own worktree, then repeat
the audit.

Attribute a post-merge regression before editing. Route it to the responsible
worker; when attribution is ambiguous, stop and inspect the interaction rather
than letting the coordinator patch the integration worktree.

After three repeats of the same conflict or gate signature without evidence of
progress, record the attempts and escalate.

## Cleanup checklist

Remove a campaign worktree only after its final commit and merge are reachable
from the integration branch, its path exactly matches the campaign state, it is
clean, and the post-merge gate passed. Do not use forced removal. Delete a local
campaign branch only after `git branch --merged` proves it merged. Preserve and
report anything that fails these checks.
