# Crawl & Render Specialist Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/crawl-render-specialist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/crawl-render-specialist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/crawl-render-specialist/HEARTBEAT.md`

## External services

### Crawl tooling (Screaming Frog / Sitebulb / equivalent)
- **Purpose:** Crawl, render, internal link, redirect, hreflang, status code audits.
- **Access:** Local CLI / desktop license.
- **Convention:** JS rendering enabled by default for audit-tier engagements.

### Log-file analysis tooling
- **Purpose:** Crawl-budget analysis, bot behavior, soft-404 patterns.
- **Access:** Per-engagement log access via account-manager.
- **Convention:** Raw outputs filed under `engagements/<client>/technical/logs/`.

## Conventions

- Outputs follow the audit-template column set, including the impact column.
- Render-vs-crawl divergence is escalated same-day to the Tech SEO Lead.
