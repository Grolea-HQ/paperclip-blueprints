# Staff Writer Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/staff-writer/`
- Editorial folder: `editorial/` — read access; I write into `editorial/issues/` and `editorial/background/`.
- Citations workspace: `editorial/citations/<issue-date>.md` — one file per issue, my responsibility.
- Voice guide: `editorial/voice-guide.md` (read every assignment).
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/staff-writer/memory/`.

## Conventions

- Every claim I introduce carries a citation entry — link, retrieved-on date, primary vs. secondary source flag.
- I never push assembly directly to the Newsletter Producer — only the Managing Editor opens that handoff.
- I log every assignment received and shipped to the editor in `agents/staff-writer/memory/<date>.md`.
