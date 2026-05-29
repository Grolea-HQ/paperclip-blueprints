# Analyst Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/analyst/`
- Analytics baselines: `clients/<client-slug>/analytics/baseline.md`
- Datasets: `clients/<client-slug>/analytics/datasets/<YYYY-MM>/`
- Data-quality log: `clients/<client-slug>/analytics/dq-log.md`
- Own runtime journal: `agents/analyst/HEARTBEAT.md`

## Skills loaded

- `client-reporting-pack` — what data the monthly report needs.
- `monthly-strategy-review` — what data the Plan-week and QBR require.

## External services

Analytics tools (GA4, ad platform reports, ESP reports, social platform reports) accessed via each client's own accounts after the Founder wires credentials post-import. No platform credentials are stored in this package.

## Conventions

- Every dataset is dated, sourced, and reproducible (note the query, the date pulled, the platform).
- Data-quality log entries: source, issue, severity, who flagged, resolution status.
- Attribution methods documented per client so they're defensible at QBR.
