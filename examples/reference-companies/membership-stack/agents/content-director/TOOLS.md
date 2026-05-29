# Content Director Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/content-director/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/content-director/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/content-director/HEARTBEAT.md`

## Content paths

- Release calendar: `content/release-calendar.md`
- Atomic notes per release: `content/atomic-notes/<release-slug>.md`
- Editorial style guide: `content/style-guide.md`
- Content positioning doc: `content/positioning.md`

## Conventions

- Friday is the hand-off deadline for the next Monday release.
- Slot-type swaps require CEO approval, never Monday-morning improvisation.
