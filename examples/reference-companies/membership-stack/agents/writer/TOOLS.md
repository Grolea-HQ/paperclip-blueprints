# Writer Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/writer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/writer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/writer/HEARTBEAT.md`

## Content paths

- Long-form guides: `library/guides/<category>/<guide-slug>/`
- Email copy: `marketing/emails/<sequence-slug>/`
- Atomic notes (handed in with each draft): `content/atomic-notes/<release-slug>.md`

## Conventions

- Draft files Fridays for the Monday release.
- Voice and positioning rules in `content/style-guide.md` and `content/positioning.md`.
- Never claim specific member outcomes; never frame an asset as a one-time purchase.
