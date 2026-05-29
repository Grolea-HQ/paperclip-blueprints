# Ad Ops Specialist Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/ad-ops-specialist/`
- Monetization subtree:
  - `monetization/ad-ops-sop.md`
  - `monetization/utm-scheme.md`
  - `monetization/sponsor-campaigns/<advertiser-date>.md` — one file per campaign.
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/ad-ops-specialist/memory/`.

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** Traffic sponsor copy into the live issue, configure tracking, and pull click reports.
- **Access:** ESP web UI; credentials owned by the Newsletter Producer who applies the changes I prepare.
- **Convention:** I never publish a sponsored issue myself. I prepare the slot and copy; the Newsletter Producer ships.

## UTM scheme

- Standing scheme: `?utm_source=newsletter-press&utm_medium=sponsorship&utm_campaign=<advertiser-slug>&utm_content=<slot>-<YYYYMMDD>`.
- Validate with a UTM-builder before publishing.

## Conventions

- Every traffic check-in carries: deal ID, advertiser, slot, date, copy hash.
- Every post-campaign report includes: impressions (sends), unique opens, sponsor clicks, sponsor CTR, comparable issue CTR baseline.
- I never paste sponsor brand assets, contract details, or advertiser internal data into Paperclip comments.
