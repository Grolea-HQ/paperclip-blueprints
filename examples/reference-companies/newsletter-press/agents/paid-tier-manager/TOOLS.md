# Paid Tier Manager Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/paid-tier-manager/`
- Monetization subtree: `monetization/welcome-sequence.md`, `monetization/paid-funnel.md`, `monetization/pricing-brief-<date>.md`, `monetization/retention-review.md`.
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/paid-tier-manager/memory/`.

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** Configure paid tier, trial flow, welcome automations.
- **Access:** ESP web UI; the Newsletter Producer owns the credentials and pushes changes I propose.
- **Convention:** I never push changes to live automations on my own. I document the change in `monetization/`, hand the file to the Newsletter Producer, and the Producer ships.

## Stripe (or ESP-native payments)

- **Purpose:** Read paid-tier MRR, churn, and conversion data.
- **Access:** Stripe dashboard in read-only mode (or ESP native — Substack uses its own).
- **Convention:** I never change price points in Stripe. The Founder signs off; the Newsletter Producer pushes the change in the ESP.

## Conventions

- Every pricing proposal carries: current state, proposed change, projected impact on MRR, projected impact on retention, and a rollback plan.
- I never paste real subscriber emails, payment data, or Stripe IDs into Paperclip comments.
