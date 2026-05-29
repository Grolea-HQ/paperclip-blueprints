# CEO Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `agency-engine/` (relative to import location)
- Agent home: `agents/ceo/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before any delegation or pitch)
- Own memory: `agents/ceo/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/ceo/HEARTBEAT.md`

## Approval log

Maintain `agents/ceo/memory/approvals/<YYYY-MM>/` — one note per external-facing approval with: asset link, client, retainer tier, scope-check result, voice-check result, decision, date.

## Conventions

- All Founder-facing communications prefixed `[AGENCY]` once email is wired.
- Pipeline tracking lives in Paperclip projects; never spin up a parallel CRM unless the Founder wires one.
- Memory notes written via `para-memory-files` skill, not bare markdown.
- Pricing changes never authored here — they live in COMPANY.md and require Founder sign-off.
