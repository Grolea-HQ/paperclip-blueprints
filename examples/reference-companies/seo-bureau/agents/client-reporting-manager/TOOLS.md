# Client Reporting Manager Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/client-reporting-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/client-reporting-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/client-reporting-manager/HEARTBEAT.md`

## External services

### Dashboard tooling (Looker Studio / equivalent)
- **Purpose:** Apply narrative + brand layer on top of the Reporting Engineer's data shells.
- **Access:** Per-engagement workspace.
- **Convention:** Branded vs. white-label per the engagement letter.

## Conventions

- Production schedule: 27th narrative, 28th–last business day QA, 1st delivery.
- Late-report risk escalated to the Head of Accounts same-day.
- No branded/white-label mixing in one report.
- Findings: three bullets. Next-month focus: one bullet.
