# CEO Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/ceo/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/ceo/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/ceo/HEARTBEAT.md`

## Conventions

- Daily status to the Founder by 18:00 weekdays.
- Weekly retainer health review every Monday 09:00.
- Read `PROJECT-INVENTORY.md` before approving any new deliverable.
- Memory notes via the `para-memory-files` skill, not bare markdown.
