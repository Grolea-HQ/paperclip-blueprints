# Community Manager Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/community-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/community-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/community-manager/HEARTBEAT.md`

## Browser automation

Use the **`dev-browser`** skill for any task requiring browser interaction (billing-provider dashboard, member-portal QA, community-platform admin). Load the skill for server start commands and usage patterns.

## Community paths

- Community policy: `community/policy.md`
- Moderation log: `community/moderation-log.md`
- Weekly digest: `community/digests/<YYYY-WW>.md`
- Welcome DM template: `community/welcome-dm.md`

## Conventions

- Monday announcement at 09:30.
- New-member welcome DM within 24 hours.
- Ban decisions escalate to the CEO; warnings and soft mutes handled directly.
