# Billing Specialist Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/billing-specialist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/billing-specialist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/billing-specialist/HEARTBEAT.md`

## Billing paths

- Billing config: `operations/billing-config.md`
- Failed-renewal events log: `operations/billing-events.md`
- Refund log: `operations/refunds/<YYYY-MM>.md`
- Affiliate payout reconciliation: `operations/affiliate-recon/<YYYY-MM>.md`
- Quarterly reconciliation: `operations/reconciliation/<YYYY-Q>.md`

## Conventions

- Refunds inside the 14-day window processed same-day; outside escalates to Member Success Lead → CEO.
- Affiliate payouts run the first business day, reconciled.
- Chargeback notices filed to the CEO immediately.
