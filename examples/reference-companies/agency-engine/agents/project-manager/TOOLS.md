# Project Manager Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/project-manager/`
- Run-week queues: `clients/<client-slug>/run-week/<YYYY-MM>.md`
- Stand-up notes: `agents/project-manager/memory/standups/<YYYY-MM-DD>.md`
- Scope-creep log: `clients/<client-slug>/scope-creep.md`
- Own runtime journal: `agents/project-manager/HEARTBEAT.md`

## Skills loaded

- `scope-of-work-builder` — translating Plan-week outputs into Run-week task queues.
- `scope-creep-recovery` — capture, triage, change-order conversion.
- `creative-qa-pipeline` — QA checklist for every external deliverable.

## Conventions

- Stand-ups are logged the same day; if a stand-up didn't happen, that's a flag in itself.
- Every scope-creep finding is captured within 24h, with: ask, source (client direct / channel lead), in-scope ruling, proposed change order, owner.
- QA sign-off is recorded on each deliverable before Account Manager takes it.
