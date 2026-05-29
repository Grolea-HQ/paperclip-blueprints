# Account Manager Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/account-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/account-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/account-manager/HEARTBEAT.md`

## Email

Use the standard client-communication channel approved by the Head of Accounts and the CEO. Do not adopt new tools without sign-off. Client-facing emails are the only outbound channel an Account Manager owns.

## Conventions

- 30-day onboarding checklist is a gate, not a guideline.
- Monthly report delivery is the first business day of each month.
- Weekly check-in notes filed under `accounts/<client>/check-ins/`.
