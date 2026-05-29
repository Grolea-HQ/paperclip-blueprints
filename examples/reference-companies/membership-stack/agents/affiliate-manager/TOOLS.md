# Affiliate Manager Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/affiliate-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/affiliate-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/affiliate-manager/HEARTBEAT.md`

## Email

Communication channel TBD; once the Founder enables email, use the standard sender configuration. All outgoing Founder emails MUST include `[MS]` at the start of the subject so threads route correctly.

- Sender account: `<set at runtime by Founder>`
- Founder email: `<set at runtime by Founder>`

## Affiliate paths

- Affiliate roster: `marketing/affiliates/roster.md`
- Application screening log: `marketing/affiliates/applications-log.md`
- Monthly payout sheets: `marketing/affiliates/payouts/<YYYY-MM>.md`
- Promo-claim audit log: `marketing/affiliates/claim-audit-log.md`

## Conventions

- Payouts run on the first business day of each month.
- Lifetime deal referrals excluded from payouts by policy.
- Terminations for fraud or false claims handled directly; other terminations escalate to CMO.
