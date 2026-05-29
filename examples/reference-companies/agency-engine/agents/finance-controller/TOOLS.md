# Finance Controller Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/finance-controller/`
- Profitability: `finance/profitability/<YYYY-MM>.md`
- Pricing defensibility memos: `finance/pricing-defensibility/<YYYY-Q>.md`
- Pitch sanity checks: `finance/pitch-sanity/<client-slug>-<YYYY-MM-DD>.md`
- Watchlist: `finance/watchlist.md`
- Own runtime journal: `agents/finance-controller/HEARTBEAT.md`

## Skills loaded

- `pricing-and-proposal-templates` — pricing-tier defensibility framework.
- `retainer-pitch-authoring` — financial sanity-check on pitches.

## External services

Financial systems (banking, accounting, payments) are accessed via the Founder's wired credentials post-import. No financial credentials are stored in this package.

## Conventions

- Monthly profitability follows the Bookkeeper's Day 1-5 close by no more than 48 hours.
- Watchlist updated weekly during the back half of the month.
- Pricing-tier defensibility memos archived per quarter for QBR cross-reference.
