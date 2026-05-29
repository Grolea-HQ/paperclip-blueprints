# Brand Designer Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/brand-designer/`
- Visual system docs: `clients/<client-slug>/visual-system.md`
- Deliverables: `clients/<client-slug>/creative/<YYYY-MM>/`
- Own memory: `agents/brand-designer/memory/`
- Own runtime journal: `agents/brand-designer/HEARTBEAT.md`

## Skills loaded

- `creative-qa-pipeline` — pre-submission self-check before handoff to Creative Director.
- `brand-voice-capture` — visual half of voice/visual capture at onboarding.

## Conventions

- File naming: `<client-slug>__<channel>__<format>__<cycle>__<version>.<ext>`.
- Visual-system doc versioned per quarter; deltas listed at top.
- All deliverables submitted to Creative Director for QA before passed to channel leads.
