# Bookkeeper Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/bookkeeper/`
- Books: `finance/books/<YYYY-MM>.md`
- Monthly P&L: `finance/pnl/<YYYY-MM>.md`
- Payout schedule: `finance/payouts.md`
- Own runtime journal: `agents/bookkeeper/HEARTBEAT.md`

## Skills loaded

- `pricing-and-proposal-templates` — referenced for SOW-to-revenue mapping discipline.

## External services

Bookkeeping platform (QuickBooks, Xero, Wave, etc.) is wired by the Founder after import. No accounting credentials are stored in this package.

## Conventions

- Day 1-5 close cadence is sacred.
- Categorization map versioned at `finance/categorization-map.md` — never change a category without Finance Controller sign-off.
- Vendor invoice over $500 routes to Finance Controller before approval.
