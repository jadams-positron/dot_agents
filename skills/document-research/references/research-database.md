# Reliability & Orchestration Research — database, schema, conventions

The research database lives in the **Orchestration** Notion teamspace under a hub page.
Always `fetch` the database before writing to confirm the current data source ID and
option values — the IDs below are a starting point and can drift.

## Locations (as of 2026-07-24)

- **Research hub page:** `https://app.notion.com/p/3a7d132d3cfd81fcbf59dfb7240be9fe`
- **Database:** `https://app.notion.com/p/5f19755d38504a32bce245fa2c581f93` (title "Reliability & Orchestration Research")
- **Data source (parent for new rows):** `collection://ed7f8826-2dcf-4bac-b733-a1c344090287`
- **Relation targets:**
  - `Resulted in ADR` → ADRs data source `6c964bdc-ccaa-4d73-aa55-4c2d0dc6ff26`
  - `Known Issue` → Known Issues data source `37bd132d-3cfd-80f0-9d0e-000bec560ff2`

The database is single-data-source, so `data_source_id` and `database_id` both work as a
parent; prefer `data_source_id` (the `collection://…` id) for `notion-create-pages`.

## Schema

| Property | Type | Notes |
|---|---|---|
| `Name` | title | The question-first title. Required. |
| `Type` | select | One of: `Investigation`, `Evaluation`, `Design Exploration`, `Spike`, `Benchmark`, `Survey`. |
| `Status` | select | One of: `Proposed`, `In Progress`, `Concluded`, `Parked`, `Superseded`. |
| `Question` | text | The research question, one or two sentences. |
| `TL;DR` | text | Bottom line. **Required when `Status = Concluded`.** |
| `Area` | multi_select | Zero or more of: `Security`, `Runtime`, `Certs/mTLS`, `Networking`, `Vault`, `Consul`, `Nomad`, `Caddy`, `Storage`, `Observability`. |
| `Owner` | person | JSON array of Notion user IDs (resolve with `notion-get-users`). |
| `Started` | date | When work began. |
| `Concluded` | date | When concluded. |
| `Last Reviewed` | date | Bump to today on every update. |
| `Tracking` | url | Outcome / tracking link (GitHub issue, PR, doc). **An outcome link is required alongside TL;DR when concluding.** |
| `Resulted in ADR` | relation | Two-way → ADRs. Populate if the research produced an ADR. |
| `Known Issue` | relation | Two-way → Known Issues. Populate if it maps to a known issue. |

### Setting properties (create/update payload)

Property values are a JSON map of property name → SQLite value:

- Selects: the option string, e.g. `"Type": "Investigation"`, `"Status": "Concluded"`.
- Multi-select: array of strings, e.g. `"Area": ["Runtime"]`.
- Person: array of user IDs, e.g. `"Owner": ["331d872b-594c-8186-91cc-0002f863c611"]`.
- Text / url: plain string.
- **Dates use expanded property names**, not the bare name:
  - `"date:Started:start": "2026-07-23"`
  - `"date:Concluded:start": "2026-07-24"`
  - `"date:Last Reviewed:start": "2026-07-24"`
  - (`:end` only for ranges; `:is_datetime` = 1 for datetimes, else 0/omit.)
- Relations: array of page URLs in the related data source (`fetch` that source to find target pages).

## Conventions (teamspace rules — do not violate)

- **One row per research effort.** Types: Investigation / Evaluation / Design Exploration / Spike / Benchmark / Survey.
- **Question-first titles.** Phrase the title as the question the research answers, e.g. "What bounds how many models fit on an FPGA card…?" — not "FPGA fit research".
- **Concluded requires a TL;DR and an outcome link** (`Tracking`). Do not mark Concluded without both.
- **No numbered section scheme anywhere in the teamspace.** The old "05/10/20/30/40" numbering was removed; never reintroduce numbered sections or numbered cross-references. Use descriptive headers.
- **MEP docs are out of scope for Research** (team ruling) — they stay in Working Docs. Do not create MEPs here.
- **Index-row rule:** a doc primarily tracked in another database (Intake, SSI Follow-up, Known Issues) gets a lightweight index row in Research that links out; it is never moved out of its home tracker.
- **Teamspace-parent API limitation:** the API cannot create pages at the teamspace top level. Creating a row under the data source (what this skill does) works fine; only free-standing top-level teamspace pages hit the limitation and need a human to drag them out.

## Recommended research-doc skeleton

Adapt to the effort; drop sections that do not apply. Lead with the answer, cite everything.

- A **bottom-line callout** (green background) stating the answer in 2–4 sentences — mirrors the `TL;DR` property.
- **Why this matters** — the operational stakes / what triggered the research.
- **Findings** — the core result, one descriptive `##` header per theme, every load-bearing claim carrying a `file:line` (with ref/commit), PR/issue number, or source link.
- **Validation / data** — a `<table>` of the evidence (measurements, calibration points, fit/no-fit results) where applicable.
- **Caveats and boundaries** — where the conclusion stops holding (version drift, config regimes, assumptions), in a callout or bullets.
- **Corrections to prior assumptions** — beliefs this research overturned, each with why.
- **Implications** — what to do with the result; link the tracking issue/PR/MEP.
- **Method and provenance** — how the research was done (e.g. multi-agent fan-out with adversarial verification), enough for a reader to gauge confidence.
- **Key source references** — a grouped list of the load-bearing citations.
