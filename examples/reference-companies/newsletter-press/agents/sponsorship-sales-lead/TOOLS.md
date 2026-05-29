# Sponsorship Sales Lead Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/sponsorship-sales-lead/`
- Monetization subtree: `monetization/sponsor-pipeline.md`, `monetization/rate-card.md`, `monetization/sponsor-outreach.md`, `monetization/sponsorship-retro-<quarter>.md`.
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/sponsorship-sales-lead/memory/`.

## Conventions

- Every pipeline row carries: advertiser name, stage, slot, date, price, last touch.
- Every contracted deal carries an executed-deal-ID and a link to the signed contract (off-platform; I never paste contract PDFs into Paperclip).
- I never paste advertiser contact details or pricing negotiations into Paperclip comments — those live in `monetization/sponsor-pipeline.md`.
- The rate card refresh is scheduled the first Monday of each quarter.
