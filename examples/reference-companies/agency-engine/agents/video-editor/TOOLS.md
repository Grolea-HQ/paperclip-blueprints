# Video Editor Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/video-editor/`
- Deliverables: `clients/<client-slug>/video/<YYYY-MM>/`
- Rights log: `clients/<client-slug>/video/rights-log.md`
- Templates: `clients/<client-slug>/video/templates/`
- Own runtime journal: `agents/video-editor/HEARTBEAT.md`

## Skills loaded

- `creative-qa-pipeline` — pre-submission self-check.
- `brand-voice-capture` — voice for VO and on-screen text matches doc.

## Conventions

- File naming: `<client-slug>__<channel>__<format>__<cycle>__<version>.mp4`.
- Every track/clip recorded in rights log with source and license terms.
- Video templates versioned quarterly with deltas noted.
