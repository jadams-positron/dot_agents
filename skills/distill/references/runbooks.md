# Runbooks

Treat a runbook as an executable safety artifact, not merely prose.

## Preserve Operational Safety

- State the trigger and impact before the procedure.
- Preserve prerequisites, access requirements, cautions, command order,
  decision points, expected output, validation, rollback, escalation, and
  ownership that operators need.
- Verify commands and observed behavior against the current implementation.
  Do not turn guesses into instructions.
- Use explicit placeholders for site-, host-, account-, and secret-specific
  values.
- Keep failure branches beside the step that can fail.
- Update indexes, navigation, alerts, links, and other consumers that locate or
  depend on the runbook.
- Validate both the source and the rendered or published form when the
  repository provides a documentation site.

## `api.positron.ai` Operator Manual

For runbooks in
`~/code/github/positron-ai/api.positron.ai/`, inspect the live repository
instructions and site configuration before editing. The current integration is:

1. Keep operator runbooks under `docs/manual/runbooks/`; Zensical publishes
   `docs/manual/`, while developer docs under `docs/*.md` stay outside the site.
2. Add or retain the runbook in the **Troubleshooting → Runbooks** navigation
   in `zensical.toml`.
3. Update `docs/manual/troubleshooting/runbooks.md` and relevant task-oriented
   manual pages so operators can find the procedure. Update `README.md` and
   `AGENTS.md` when their documentation indexes should expose it.
4. Follow every repository-specific dependency. For an alert runbook, follow
   `AGENTS.md`'s alert workflow and keep alert links, generated goldens, and
   runbook-link tests consistent.
5. Run `just manual-build` to build the site into ignored `site/`. Use
   `just manual` when visual inspection or live preview is useful.
6. Run the narrowest relevant documentation tests, including
   `uv run python -m pytest tests/test_runbook_present.py` when alert-runbook
   links or its asserted content are affected.
7. Confirm the `Publish Manual` workflow still covers the changed source or
   configuration. Normal pushes to `develop` that change `docs/manual/**` or
   `zensical.toml` build and deploy the site to GitHub Pages; do not commit
   generated `site/`.

Re-read these paths rather than treating this snapshot as immutable. Preserve
newer repository conventions when they differ.
