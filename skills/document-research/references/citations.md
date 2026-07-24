# Citations — mandatory, specific, clickable

Every load-bearing claim in a research doc **must** carry a specific, clickable citation.
Bare `file:line` strings, channel names, or "per Slack" are not acceptable. Prefer permanent,
pinned links so a reader lands on the exact evidence months later. Citations may be inline or
collected in a "Key source references" section at the bottom (or both) — but they must exist.

## GitHub source (file + line) — commit-pinned, always

Format:

```
https://github.com/<org>/<repo>/blob/<FULL_40_CHAR_COMMIT_SHA>/<path>#L<start>-L<end>
```

- **Pin to a commit SHA, never a branch.** `.../blob/main/...#L413` rots the instant a line is
  inserted above it. Get the SHA: `git rev-parse origin/main` (or whichever ref was read).
- **The line numbers must match that SHA.** This is the trap: a local clone may be many commits
  behind its remote, so line numbers read from the working tree (via editor/`Read`/`rg`) can be
  wrong for the commit being linked. Get the numbers *at the pinned commit* instead:
  `git grep -n '<anchor token>' <sha> -- <path>`. Verify each cited line this way before linking.
- Single line: `#L52`. Range: `#L413-L433`.
- State the pin once near the top ("all links pinned to commit `925b86fd`") so inline links stay short.

## GitHub PRs, issues, commits

```
https://github.com/<org>/<repo>/pull/<n>
https://github.com/<org>/<repo>/issues/<n>
https://github.com/<org>/<repo>/commit/<sha>
```

Use these for "fixed in PR #…", "tracked by #…", "landed in commit …" claims.

## Slack messages — real permalinks

Format:

```
https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TS_DIGITS>
```

- `TS_DIGITS` = the message `ts` with the dot removed: `1777653149.110949` → `p1777653149110949`.
- `CHANNEL_ID` is the channel's ID (e.g. `C0A1FJEBBC2`), **not** its `#name`.
- The most reliable source is the `Permalink` field in a `slack_search_public_and_private`
  result — copy it directly (it also carries `?thread_ts=…&cid=…` for threaded replies, which is
  worth keeping for a reply deep in a thread). If only the channel ID and `ts` are known, construct
  the link with the format above.
- To resolve a `#name` to a channel ID, use `slack_search_channels`, or read it from a search
  result's `Channel: #name (ID: C…)` line.
- Label each Slack citation with channel, author, a short quote or paraphrase, and the date, so it
  is meaningful even before the reader clicks.

## Other sources

- Notion pages/databases: link the page URL, or use a `<mention-page>` inline.
- Dashboards, runbooks, external docs, live stat surfaces: link the canonical URL (and note the
  exact metric/path when linking a dashboard or a stats endpoint).

## Discipline checklist

- [ ] Every quantitative claim, quoted statement, and "the code does X" assertion has a citation.
- [ ] All source-code links are commit-pinned, with line numbers verified at that commit.
- [ ] Slack links use channel ID + `ts`, not `#name`, and carry author + date + gist.
- [ ] A reader who clicks nothing still learns the source (author/file/PR named in text).
