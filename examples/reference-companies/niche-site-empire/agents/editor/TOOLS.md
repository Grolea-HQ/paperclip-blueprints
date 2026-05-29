# Editor Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/editor/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/editor/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/editor/HEARTBEAT.md`

## Conventions

- Editorial sign-off log lives under each site's `editorial/signoff-log.md`.
- Refresh-calendar review happens Monday 10:00 with content-director.
- 5% random-sample QA is run weekly; results feed the editorial standard.
