# Repurpose Editor Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/repurpose-editor/`
- Distribution subtree:
  - `distribution/repurposing-pack-<issue-date>.md`
  - `distribution/repurposing-log.md`
- Voice guide: `editorial/voice-guide.md` (read every pack).
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/repurpose-editor/memory/`.

## Social schedulers

- **LinkedIn:** scheduled through the founder's preferred tool (Buffer, Hypefury, native scheduling) — configured by the Newsletter Producer; I push pre-approved posts.
- **X:** scheduled through the same tool or X native; I push pre-approved threads.
- **Convention:** I never log in to the founder's accounts directly. I push posts through the scheduler with the founder's signed-off integration.

## Browser automation

Use the **`dev-browser`** skill for any web-UI workflow inside the social scheduler.

## Conventions

- Every repurposed pack is timestamped and linked to its source issue.
- I never schedule a post that fails voice-guide review — I revert and re-draft.
- I never repurpose paid-tier-only content.
