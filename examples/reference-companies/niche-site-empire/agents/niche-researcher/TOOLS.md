# Niche Researcher Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/niche-researcher/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/niche-researcher/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/niche-researcher/HEARTBEAT.md`

## External services

Use only data sources the Portfolio Owner has approved. Common tools (Ahrefs, Semrush, Google Search Console exports) are referenced generically — do not hardcode account-specific paths or credentials. If a new tool is needed, request CEO approval first.

## Conventions

- Every cluster scoring memo is filed under the candidate site's content folder.
- Cannibalisation checks are run against PROJECT-INVENTORY.md before the memo is finalised.
- Cluster pipeline summary is delivered to CEO on the last Friday of the month.
