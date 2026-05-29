# Open/Click Analyst Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/open-click-analyst/`
- Analytics folder: `analytics/` — I own this subtree.
  - `analytics/post-send-<issue-date>.md`
  - `analytics/weekly-roll-up-<date>.md`
  - `analytics/subject-line-log.md`
  - `analytics/baseline.md`
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/open-click-analyst/memory/`.

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** Pull send-level open and click data.
- **Access:** ESP analytics UI in read-only mode; Producer owns send credentials.
- **Convention:** I never trigger sends or modify segments. I read, I report.

## Meta Ads Manager

- **Purpose:** Pull paid-acquisition cohort engagement and free-to-paid conversion on Meta-sourced subs.
- **Access:** Web UI in read-only mode; Paid Acquisition Lead owns the campaigns.

## Conventions

- Every report carries: send/window timestamps, denominator, source export filename, and one one-line takeaway.
- I never paste raw subscriber emails into reports.
- The shared baseline is rebuilt on the first Monday of every month — every other agent uses it.
