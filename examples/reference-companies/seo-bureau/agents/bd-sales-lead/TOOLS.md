# BD/Sales Lead Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/bd-sales-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/bd-sales-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/bd-sales-lead/HEARTBEAT.md`

## Conventions

- Weekly pipeline report to the CEO every Friday 16:00.
- Proposals filed under `sales/proposals/<prospect>/`.
- Sales audits scoped with the SEO Analyst before the proposal stage.
- Disqualified leads logged with a one-line reason.
