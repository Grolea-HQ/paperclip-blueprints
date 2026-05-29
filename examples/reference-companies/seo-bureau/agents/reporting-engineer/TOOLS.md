# Reporting Engineer Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/reporting-engineer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/reporting-engineer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/reporting-engineer/HEARTBEAT.md`

## External services

### Google Search Console + GA4
- **Purpose:** Primary data sources for every dashboard.
- **Access:** Per-client OAuth granted at onboarding.
- **Convention:** Connector health checked daily; pull date is the 25th.

### Dashboard tooling (Looker Studio / equivalent)
- **Purpose:** White-label dashboard templates per client.
- **Access:** Per-engagement workspace.
- **Convention:** Templates do not mix branded and white-label assets.

## Conventions

- Pull date: 25th of each month.
- Connector health monitored daily.
- Anomalies routed to the SEO Analyst, not into the narrative.
