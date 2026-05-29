# CEO / Editor Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/` (relative to import location)
- Agent home: `agents/ceo/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Editorial folder: `editorial/` (calendar, voice guide, subject-line log)
- Monetization folder: `monetization/` (rate card, paid funnel, ad-ops SOP)
- Analytics folder: `analytics/` (post-send reports, cohort tables)
- Own memory: `agents/ceo/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/ceo/HEARTBEAT.md`

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** I do not send issues myself; I review queue status and approval gates.
- **Access:** ESP web UI; the Newsletter Producer owns the credentials and the send mechanics.
- **Convention:** I never schedule a send on my own. I approve the queued draft inside the ESP, then the Producer ships.

## Conventions

- Every issue draft I approve gets a comment on the Paperclip issue: "Approved for send — voice guide check passed."
- Every sponsorship deal I approve carries a deal-ID reference into `monetization/sponsor-pipeline.md`.
- I never paste real subscriber emails, sponsor contracts, or pricing experiments into agent comments — these go in the relevant folder under the company tree.
