# Schema/Structured Data Specialist Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/schema-specialist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/schema-specialist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/schema-specialist/HEARTBEAT.md`

## External services

Common tools referenced generically — Google Rich Results Test, Google Search Console schema reports, Schema Markup Validator. No credentials hardcoded.

## Conventions

- All schema templates live under `portfolio/schema-templates/` and are inherited by each site.
- Validation results are recorded per-site under `<site>/technical/schema-validation-log.md`.
- Re-validation after template change happens within 24 hours.
