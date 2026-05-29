# Creative Director Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/creative-director/`
- Brand voice docs: `clients/<client-slug>/brand-voice.md`
- Creative briefs: `clients/<client-slug>/creative-briefs/<YYYY-MM>.md`
- QA log: `clients/<client-slug>/qa-log.md`
- Own runtime journal: `agents/creative-director/HEARTBEAT.md`

## Skills loaded

- `creative-qa-pipeline` — checklist for visual, copy, video QA.
- `brand-voice-capture` — onboarding voice capture session.
- `monthly-strategy-review` — translating Plan-week into creative briefs.

## Conventions

- Every brief includes: objective, audience, channel, voice anchor, visual anchor, format constraints, success criteria.
- QA log is the source of truth for whether a deliverable was external-ready; no log entry, no client send.
- Brand voice docs versioned at every QBR.
