# Account Manager Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/account-manager/`
- Client folders: `clients/<client-slug>/` (kickoff briefs, recaps, change-order log)
- Own memory: `agents/account-manager/memory/`
- Own runtime journal: `agents/account-manager/HEARTBEAT.md`

## Skills loaded

- `client-onboarding-sequence` — week-by-week onboarding flow for new retainers.
- `scope-creep-recovery` — translating client asks into change orders.
- `client-reporting-pack` — assembling and delivering the monthly report.

## Conventions

- Every client conversation is logged the same day in `clients/<client-slug>/log.md`.
- Change orders captured in `clients/<client-slug>/change-orders/<YYYY-MM-DD>.md` with: ask, in-scope vs out-of-scope ruling, pricing impact, approval status.
- First-time sends on new commercial topics require CEO approval before send.
- Monthly recaps to client always reference the signed SOW deliverables.
