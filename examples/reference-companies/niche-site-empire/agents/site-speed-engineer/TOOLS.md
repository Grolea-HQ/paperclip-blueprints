# Site Speed Engineer Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/site-speed-engineer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/site-speed-engineer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/site-speed-engineer/HEARTBEAT.md`

## External services

Common tools referenced generically — PageSpeed Insights, CrUX dashboards, Cloudflare, WebPageTest. Access via the Portfolio Owner's accounts.

## Conventions

- Weekly CWV scan results live at `portfolio/cwv-log/<week>.md`.
- Publishing-freeze notifications are sent to content-director within 1 hour of CWV dropping out of green.
- Ad-stack CWV reviews happen before any sitewide ad-stack change.
