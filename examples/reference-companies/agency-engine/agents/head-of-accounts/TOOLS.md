# Head of Accounts Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/head-of-accounts/`
- Account health log: `agents/head-of-accounts/memory/account-health/<YYYY-WW>.md` (one note per weekly sweep)
- QBR briefs: `agents/head-of-accounts/memory/qbrs/<client-slug>-<YYYY-Q>.md`
- Recovery plans: `agents/head-of-accounts/memory/recovery/<client-slug>-<YYYY-MM-DD>.md`
- Own runtime journal: `agents/head-of-accounts/HEARTBEAT.md`

## Skills loaded

- `account-health-scoring` — weekly scoring rubric and red/yellow/green thresholds.
- `quarterly-business-review-templates` — QBR agenda, brief, deck outline.
- `churn-prevention-playbook` — recovery plays per failure mode.

## Conventions

- Weekly account health log is the first thing posted in Paperclip each Monday before 09:00.
- Red accounts trigger an immediate CEO comment, never a queued status update.
- All client-facing materials route through `account-manager` and require CEO approval before send.
