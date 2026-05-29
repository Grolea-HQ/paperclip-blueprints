# Paid Media Lead Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/paid-media-lead/`
- Audits: `clients/<client-slug>/paid/audits/<YYYY-MM-DD>.md`
- Monthly plans: `clients/<client-slug>/paid/plans/<YYYY-MM>.md`
- Friday roll-ups: `agents/paid-media-lead/memory/fridays/<YYYY-WW>.md`
- Own runtime journal: `agents/paid-media-lead/HEARTBEAT.md`

## Skills loaded

- `ad-account-audit` — onboarding audit framework.
- `monthly-strategy-review` — translating Plan-week into paid plans.
- `client-reporting-pack` — paid section of monthly report.

## External services

External ad platforms (Meta, Google, LinkedIn, TikTok) are accessed via each client's own ad accounts after the Founder wires credentials post-import. No platform credentials are stored in this package.

## Conventions

- Every monthly plan declares: budget by line, objective by line, audience definition, creative count by format, success thresholds.
- Friday roll-up format: spend, primary metric, deltas vs. plan, risks, next-week change list.
- Threshold-based pause rules documented in each plan.
