# Editor Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/editor/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/editor/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/editor/HEARTBEAT.md`

## Conventions

- Briefs reviewed against the content-brief-templates skill end-to-end.
- Drafts filed under `engagements/<client>/content/drafts/`.
- Editorial QA checklist applied to every draft. No exceptions.
- Two revision cycles max before escalating to the Content Strategist.
