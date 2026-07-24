# Notion-flavored Markdown — gotchas for research docs

Read the authoritative, live spec first: the MCP resource `notion://docs/enhanced-markdown-spec`
(via the resource-reading interface — do **not** pass that URI to a URL fetcher). This file is a
summary of the parts that bite when writing a research doc; the live spec wins if they differ.

## Escaping (outside code blocks)

Escape these with a backslash when they should render literally: `\ * ~ \` $ [ ] < > { } | ^`.
In practice, the cheapest way to avoid escaping pain is to put anything with special characters —
hex constants, `file:line` refs, code identifiers, expressions — inside inline code spans
(`` `like this` ``). Inside fenced code blocks, do **not** escape anything; write it literally.

## Tables

Notion Markdown does **not** accept pipe (`|`) tables. Use the XML form:

```
<table fit-page-width="true" header-row="true">
	<tr>
		<td>Header A</td>
		<td>Header B</td>
	</tr>
	<tr>
		<td>cell</td>
		<td>**bold cell**</td>
	</tr>
</table>
```

- Cells hold **rich text only** — no headings, lists, or code blocks inside a cell. Use `**bold**`, not HTML tags.
- Attributes (`fit-page-width`, `header-row`, `header-column`) are optional and default to false.

## Blocks that make a research doc readable

- **Callout** (great for the bottom-line and for caveats):
  ```
  <callout icon="🎯" color="green_bg">
  	**Bottom line.** …
  </callout>
  ```
  Children must be indented. Use Notion Markdown inside (`**bold**`), not HTML.
- **Columns** (e.g. a predict-vs-measure comparison):
  ```
  <columns>
  	<column>…</column>
  	<column>…</column>
  </columns>
  ```
- **Code block** — set the language when known; content is literal (no escaping):
  ````
  ```cpp
  constexpr size_t hbm_capacity = 0x4000'0000;
  ```
  ````
- **Divider:** `---`. **Headings:** `##` / `###` (5–6 collapse to 4). **Empty line:** `<empty-block/>` on its own line (plain blank lines get stripped).
- **Inline math:** `` $`equation`$ ``. **Block math:** `$$` on its own lines.

## Mentions

- User: `<mention-user url="{{user://<id>}}"/>` — but for the `Owner` *property*, pass the user ID in the properties map, not a body mention.
- Page / database: `<mention-page url="{{…}}">Title</mention-page>` links inline. Do **not** use a `<page>` block to reference an existing page — that *moves* it into the current page.
- Date: `<mention-date start="YYYY-MM-DD"/>`.

## Title placement

Do not put the page title as an `#` heading at the top of the body — the title lives in the
`Name` property. Start the body with the bottom-line callout or first section.
