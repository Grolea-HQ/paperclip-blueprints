# Paid Acquisition Lead Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/paid-acquisition-lead/`
- Growth subtree: `growth/meta-performance.md`, `growth/meta-creative-library.md`, `growth/landing-page-log.md`.
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/paid-acquisition-lead/memory/`.

## Meta Ads Manager

- **Purpose:** Run, monitor, and pause Meta campaigns; pull CAC and frequency reports.
- **Access:** Web UI; credentials owned by the Founder.
- **Convention:** Every campaign is tagged with the creative ID and the audience ID — never run an untagged campaign. Pause within 24h of a CAC ceiling breach.

## Browser automation

Use the **`dev-browser`** skill for any web-UI workflow inside Meta Ads Manager (campaign duplication, audience exports, creative uploads).

## Conventions

- Every creative variant carries a one-line voice-and-offer note before it goes to the CEO for approval.
- I never paste ad-account credentials, audience exports, or pixel data into Paperclip comments. Those stay in the relevant folder.
- I run a pixel/UTM audit on the first Monday of every month.
