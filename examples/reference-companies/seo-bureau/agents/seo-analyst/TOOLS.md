# SEO Analyst Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/seo-analyst/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/seo-analyst/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/seo-analyst/HEARTBEAT.md`

## External services

### Google Search Console
- **Purpose:** Indexation, coverage, performance, manual actions, rich results.
- **Access:** Per-client OAuth.
- **Convention:** Daily algorithm-update watch reviews queries and coverage deltas.

### GA4
- **Purpose:** Sessions, conversions, channel attribution, landing-page cluster performance.
- **Access:** Per-client OAuth.
- **Convention:** Anomalies cross-checked against GSC before escalation.

### Algorithm-update sources (Google Search Status Dashboard, industry trackers)
- **Purpose:** Confirm update windows.
- **Access:** Public web.
- **Convention:** Diagnoses cite the confirmed window, not the rumor.

## Conventions

- Diagnostic raw outputs filed under `engagements/<client>/analytics/diagnostics/`.
- Daily algorithm-update watch logged in memory notes via the `para-memory-files` skill.
