# Director of Operations Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `agency-engine/` (relative to import location)
- Agent home: `agents/director-of-operations/`
- Operating manual: `OPERATIONS.md` (re-read every Monday)
- Project inventory: `PROJECT-INVENTORY.md` (read before approving any new task)
- Own memory: `agents/director-of-operations/memory/`
- Own runtime journal: `agents/director-of-operations/HEARTBEAT.md`

## Delivery tracking

- Weekly capacity sheet lives at `agents/director-of-operations/memory/capacity/<YYYY-WW>.md`.
- Daily delivery-status notes at `agents/director-of-operations/memory/daily/<YYYY-MM-DD>.md`.
- Use the `para-memory-files` skill to manage these — do not author bare markdown.

## Conventions

- Daily delivery status to CEO is sent every weekday by 18:00 local.
- All cross-department coordination logged in Paperclip comments, never in side channels.
- Resourcing conflicts logged with: agent, client, deliverable, current cycle stage, proposed resolution.
