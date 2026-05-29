# Managing Editor Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/managing-editor/`
- Editorial folder: `editorial/` — I own this subtree.
  - `editorial/calendar.md` — 4-week-ahead calendar.
  - `editorial/voice-guide.md` — refreshed every 4 sends.
  - `editorial/subject-line-protocol.md`
  - `editorial/issues/<YYYY-MM-DD>.md` — one file per issue.
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating).
- Own memory: `agents/managing-editor/memory/` (daily notes — `para-memory-files` skill).
- Own runtime journal: `agents/managing-editor/HEARTBEAT.md`.

## Conventions

- I never schedule a send in the ESP. I hand the approved file to the Newsletter Producer.
- I never publish the editorial calendar outside the company tree. It contains in-progress angles.
- Voice-guide updates always carry a date stamp and a one-line rationale (e.g., "2026-05-20 — added 'never use the word community'").
