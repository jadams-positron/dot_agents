// Reusable PR-description cleanup workflow.
// Invoke via: Workflow({ scriptPath: "<this file>", args: { pr: <number> } })
// Map changed files into review areas -> deep-read each vs git -> draft an accurate
// description (with a How to Review) -> adversarially verify every claim against the diff.

export const meta = {
  name: 'pr-description-cleanup',
  description: 'Inventory a PR diff, draft a clear+accurate description with a How-to-Review, adversarially verify vs git',
  phases: [
    { title: 'Map', detail: 'cluster changed files into review areas' },
    { title: 'Inventory', detail: 'parallel deep-read of each area vs git' },
    { title: 'Draft', detail: 'synthesize the cleaned description' },
    { title: 'Verify', detail: 'multi-lens adversarial check vs the diff' },
  ],
}

const PR = args && args.pr
if (!PR) throw new Error('pass args: { pr: <PR number> }')

const CTX = `Target: PR #${PR} in this repo. Resolve specifics yourself with gh/git:
- slug:    gh repo view --json nameWithOwner --jq .nameWithOwner
- head:    gh pr view ${PR} --json headRefOid --jq .headRefOid
- base:    gh pr view ${PR} --json baseRefName --jq .baseRefName   (diff base = origin/<base>)
- body:    gh pr view ${PR} --json body --jq .body
IMPORTANT: the git working tree may be checked out on a DIFFERENT branch/commit than the PR head, so the Read tool can show the wrong files. Read PR content via git against the resolved head SHA only: \`git show <head>:<path>\` for a file, \`git diff origin/<base> <head> -- <path>\` for a change.`

const MAP_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    stat: { type: 'string', description: 'files changed / +insertions / -deletions' },
    areas: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          name: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          intent: { type: 'string' },
        },
        required: ['name', 'files', 'intent'],
      },
    },
  },
  required: ['stat', 'areas'],
}

const INVENTORY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    area: { type: 'string' },
    groundTruth: { type: 'array', items: { type: 'string' } },
    inaccuraciesInCurrentBody: { type: 'array', items: { type: 'string' } },
  },
  required: ['area', 'groundTruth', 'inaccuraciesInCurrentBody'],
}

const DRAFT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { markdown: { type: 'string', description: 'cleaned PR body, ending at the trailer; NO auto-generated tool block' } },
  required: ['markdown'],
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    lens: { type: 'string' },
    issues: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          location: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'location', 'problem', 'fix'],
      },
    },
    verdict: { type: 'string' },
  },
  required: ['lens', 'issues', 'verdict'],
}

phase('Map')
const map = await agent(
  `${CTX}\n\nResolve base/head, then run \`git diff origin/<base>...<head> --stat\`. Cluster the changed files into 3-6 coherent REVIEW AREAS (by subsystem/intent, not raw directory). Each area: a short name, the files it covers, and the intent in a phrase. Also return the overall stat line.`,
  { label: 'map', phase: 'Map', schema: MAP_SCHEMA },
)

phase('Inventory')
const inv = (await parallel((map.areas || []).map(a => () =>
  agent(
    `${CTX}\n\nInventory the "${a.name}" area of PR #${PR} (intent: ${a.intent}). Files: ${a.files.join(', ')}.\nUsing git show/diff against the resolved head, report:\n(1) groundTruth — verified facts a reviewer/operator needs: behavioral changes; new or removed env vars (distinguish REQUIRED \`\${V:?...}\` from DEFAULTED \`\${V:-x}\`, give the default); removed/renamed ports, flags, endpoints; breaking changes; anything fail-closed.\n(2) inaccuraciesInCurrentBody — fetch the current PR body and list specific claims this area proves wrong or stale (quote them). Cite file paths.`,
    { label: `inv:${a.name}`, phase: 'Inventory', schema: INVENTORY_SCHEMA },
  ),
))).filter(Boolean)

const factsJson = JSON.stringify(inv, null, 1)

phase('Draft')
const draft = await agent(
  `${CTX}\n\nRewrite PR #${PR}'s description for CLARITY and ACCURACY. Fetch the current body for structure/intent, and use the verified inventory below (ground truth + flagged inaccuracies).\n\nProduce GitHub-flavored Markdown with these sections:\n- ## Summary — what changes and why, precise var/port names, no fluff.\n- ## How to Review — for a human facing this diff: a suggested READING ORDER that follows the change's logic (core mechanism first, then the code that enforces/guards it, then the operator-facing surface, then tests as the contract — using REAL file paths from the inventory); the 2-3 things to scrutinize most; the key mental model in 1-2 sentences; how to sanity-check locally. Skimmable bullets.\n- ## Breaking Changes / Operator Action Required — only real ones, each with the concrete action.\n- ## Validation — real, runnable checks (no machine-specific absolute paths).\n- Trailer: preserve issue links / stacking lines from the current body (e.g. \`Fixes #NNN\`, \`Stacked below #NNN\`).\n\nRules: fix EVERY flagged inaccuracy; never claim a var "defaults to X" if it is actually required; prefer correctness over preserving old wording. Do NOT include any auto-generated tool block (e.g. \`<!-- CURSOR_SUMMARY -->...<!-- /CURSOR_SUMMARY -->\`) — the caller re-appends it verbatim. End at the trailer.\nReturn ONLY the markdown body.\n\nINVENTORY (JSON):\n${factsJson}`,
  { label: 'draft', phase: 'Draft', schema: DRAFT_SCHEMA },
)

phase('Verify')
const lenses = [
  { key: 'accuracy', prompt: `Adversarially verify this DRAFT PR description against the actual diff (resolved head vs origin/<base>). For EVERY factual claim — required-vs-default env, port/flag/endpoint names, what was removed, fail-closed behavior, who-can-reach-what — check it with \`git show\`/\`git diff\`. Flag anything wrong, unverifiable, or overstated; default to flagging when uncertain.` },
  { key: 'completeness', prompt: `Review this DRAFT for OMISSIONS against \`git diff origin/<base>...<head> --stat\`. Identify any significant change, breaking change, or operator action not represented (or under-represented). Confirm each gap with git.` },
  { key: 'clarity', prompt: `Review this DRAFT purely for CLARITY/readability for a reviewer + operator: section ordering, ambiguous wording, redundancy, terminology consistency, scannability. Judge the "## How to Review" section hard — is it genuinely useful (clear reading order, real file paths, right things to scrutinize, crisp mental model) or generic filler? Quote concrete fixes. Clarity only — don't invent accuracy issues.` },
]
const verifies = (await parallel(lenses.map(l => () =>
  agent(
    `${CTX}\n\n${l.prompt}\n\nDRAFT:\n----------\n${draft.markdown}\n----------`,
    { label: `verify:${l.key}`, phase: 'Verify', schema: VERIFY_SCHEMA },
  ),
))).filter(Boolean)

const issues = verifies.flatMap(v => (v.issues || []).map(i => ({ ...i, lens: v.lens })))

return {
  draft: draft.markdown,
  issues,
  verdicts: verifies.map(v => ({ lens: v.lens, verdict: v.verdict, count: (v.issues || []).length })),
  map,
  inventory: inv,
}
