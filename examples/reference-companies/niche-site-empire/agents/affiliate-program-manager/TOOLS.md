# Affiliate Program Manager Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/affiliate-program-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/affiliate-program-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/affiliate-program-manager/HEARTBEAT.md`

## External services

Common networks referenced generically — Amazon Associates, ShareASale, Impact, CJ Affiliate. Account credentials remain with the Portfolio Owner; no credentials are hardcoded in this package.

## Conventions

- Per-site network configurations live at `<site>/monetization/affiliate-config.md`.
- Product lists for commercial briefs live in the brief itself, sourced from this agent.
- Monthly EPC report is delivered to CEO on the first Monday of the month.
