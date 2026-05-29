# Lifecycle/Email Lead Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/lifecycle-email-lead/`
- Audits: `clients/<client-slug>/lifecycle/audits/<YYYY-MM-DD>.md`
- Monthly plans: `clients/<client-slug>/lifecycle/plans/<YYYY-MM>.md`
- Flow inventory: `clients/<client-slug>/lifecycle/flow-inventory.md`
- Friday roll-ups: `agents/lifecycle-email-lead/memory/fridays/<YYYY-WW>.md`
- Own runtime journal: `agents/lifecycle-email-lead/HEARTBEAT.md`

## Skills loaded

- `monthly-strategy-review` — Plan-week translation to lifecycle plan.
- `client-reporting-pack` — lifecycle section of monthly report.
- `brand-voice-capture` — email voice anchored in captured client voice.

## External services

ESP access (Klaviyo, ActiveCampaign, HubSpot, Customer.io, etc.) routes through each client's own account after the Founder wires credentials post-import. No ESP credentials are stored in this package.

## Conventions

- Every monthly plan declares: flow priorities, broadcast cadence, segment definitions, success thresholds.
- Friday roll-up format: sends, open rate, click rate, revenue-per-recipient, deliverability flags, deltas vs. plan, next-week changes.
- Deliverability incidents logged immediately in `clients/<client-slug>/lifecycle/deliverability-log.md`.
