# Template/Asset Designer Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/template-asset-designer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/template-asset-designer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/template-asset-designer/HEARTBEAT.md`

## File formats

- Spreadsheets: Google Sheets primary; .xlsx export checked before release.
- Docs: Google Docs primary; .docx + PDF exports checked.
- Slides: Google Slides primary; .pptx export checked.

## Conventions

- Every template ships with an example pre-filled version inline.
- Cover sheet states version, intended use, time-to-fill.
- New file formats require Product Manager approval.
