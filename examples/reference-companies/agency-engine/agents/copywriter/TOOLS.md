# Copywriter Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/copywriter/`
- Voice docs: `clients/<client-slug>/brand-voice.md` (read every cycle)
- Phrasing log: `clients/<client-slug>/phrasing-log.md`
- Deliverables: `clients/<client-slug>/copy/<YYYY-MM>/`
- Own runtime journal: `agents/copywriter/HEARTBEAT.md`

## Skills loaded

- `brand-voice-capture` — voice-doc reading and per-client phrasing discipline.
- `creative-qa-pipeline` — pre-submission self-check.
- `retainer-pitch-authoring` — agency-side pitch copy.

## Conventions

- Every copy deliverable submitted with three variants where format allows.
- Voice-doc deltas at quarterly refresh logged in phrasing log.
- No commercial claims (pricing, guarantees, comparisons) without CEO sign-off via Creative Director.
