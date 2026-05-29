# Newsletter Producer Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/newsletter-producer/`
- Distribution folder: `distribution/` — I own this subtree.
  - `distribution/esp-setup.md`
  - `distribution/segments.md`
  - `distribution/deliverability-log.md`
  - `distribution/send-log.md`
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/newsletter-producer/memory/`.

## ESP (Substack / beehiiv / ConvertKit)

- **Purpose:** Schedule sends, configure segments, run subject-line tests, manage paid tier, run welcome automations.
- **Access:** ESP web UI; credentials owned by the Founder; I am the sole agent with operational write access.
- **Convention:** Every send goes through a pre-send checklist (subject-line test set, segments applied, sponsor slot trafficked, deliverability sane).

## Browser automation

Use the **`dev-browser`** skill for any web-UI workflow inside the ESP that needs scripted repetition (segment exports, automation imports, A/B test setup).

## Sending domain

- SPF, DKIM, DMARC configured on the founder's sending domain. I do not change DNS without the Founder.

## Conventions

- Every send has a row in `distribution/send-log.md` with: send time, list size, subject lines tested, winning variant.
- Every deliverability event (bounce spike, complaint, blocklist) has a row in `distribution/deliverability-log.md`.
- I never paste subscriber emails or ESP API keys into Paperclip comments.
