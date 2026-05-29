# Strategist Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/strategist/`
- Discovery briefs: `clients/<client-slug>/discovery-brief.md`
- Monthly plans: `clients/<client-slug>/plans/<YYYY-MM>.md`
- QBR briefs: `clients/<client-slug>/qbrs/<YYYY-Q>.md`
- Own memory: `agents/strategist/memory/`
- Own runtime journal: `agents/strategist/HEARTBEAT.md`

## Skills loaded

- `monthly-strategy-review` — Plan-week deliverable structure.
- `quarterly-business-review-templates` — QBR brief and deck outlines.
- `brand-voice-capture` — voice doc per client.
- `discovery-call-playbook` — discovery brief construction.

## Conventions

- Every monthly plan is dated and locked once CEO-approved; revisions become a new dated file.
- Discovery briefs are updated quarterly at QBR — they are living documents, not archives.
- Plans reference signed SOW deliverables by name.
