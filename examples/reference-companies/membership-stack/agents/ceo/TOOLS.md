# CEO Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/ceo/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/ceo/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/ceo/HEARTBEAT.md`

## Email

Communication channel TBD; once the Founder enables email, use the standard sender configuration. All outgoing Founder emails MUST include `[MS]` at the start of the subject so threads route correctly.

- Sender account: `<set at runtime by Founder>`
- Founder email: `<set at runtime by Founder>`

## Conventions

- All Founder emails prefixed `[MS]` once email is enabled.
- Memory notes written via `para-memory-files` skill, not bare markdown.
- Approval log entries written under `agents/ceo/memory/approvals/` per decision.
- Never commit secrets or machine-local paths.
