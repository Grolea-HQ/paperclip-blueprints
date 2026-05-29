# Churn Analyst Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/churn-analyst/`
- Analytics subtree (read access to the full folder; I own the cohort files):
  - `analytics/cohort-churn-<YYYY-MM>.md`
  - `analytics/cohort-table.md`
  - `analytics/cancel-reasons.md`
  - `analytics/welcome-impact-<change-date>.md`
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/churn-analyst/memory/`.

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** Pull subscription event logs (start, trial, paid, cancel) and unsubscribe reasons.
- **Access:** ESP analytics UI in read-only mode; Producer owns credentials.
- **Convention:** I never modify subscription records. I read, I report.

## Stripe (or ESP-native payments)

- **Purpose:** Pull payment events and churn reasons where the ESP does not capture them.
- **Access:** Read-only dashboard; Paid Tier Manager owns payment configuration.

## Conventions

- Every cohort report has: cohort definition, source export filename, retained-at-Day-30/60/90/365, cancel-reason cluster.
- I never paste subscriber emails, Stripe IDs, or payment details into reports.
- The cohort table is rebuilt monthly; older cohorts roll forward.
