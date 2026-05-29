# Member Success Lead Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/member-success-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/member-success-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/member-success-lead/HEARTBEAT.md`

## Email

Communication channel TBD; once the Founder enables email, use the standard sender configuration. All outgoing Founder emails MUST include `[MS]` at the start of the subject so threads route correctly.

- Sender account: `<set at runtime by Founder>`
- Founder email: `<set at runtime by Founder>`

## Member-success paths

- Onboarding tour copy: `member-success/onboarding-tour.md`
- Churn-save sequences: `marketing/churn-save/<sequence-slug>/`
- Cancel-reason log: `analytics/cancel-reasons.md`
- Quarterly survey results: `analytics/surveys/<YYYY-Q>.md`

## Conventions

- Trigger churn-save Sequences A, B, C based on event — never overlapping.
- No discounts in churn-save copy.
- Survey response patterns logged to the Retention Analyst on the same day.
