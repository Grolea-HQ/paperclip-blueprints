# Retention Analyst Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/retention-analyst/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/retention-analyst/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/retention-analyst/HEARTBEAT.md`

## Analytics paths

- Weekly cohort report: `analytics/cohort-reports/<YYYY-WW>.md`
- LTV:CAC model: `analytics/ltv-cac.md`
- Lifetime deal model: `analytics/lifetime-deal-model.md`
- Cancel reasons: `analytics/cancel-reasons.md`
- Survey readout: `analytics/surveys/<YYYY-Q>.md`

## Conventions

- Cohort report files Monday 08:30 — every week, no exceptions.
- LTV:CAC bar reviewed weekly.
- Lifetime deal models include base case, sensitivity tables, and cap.
