# Paid Acquisition Lead Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/paid-acquisition-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/paid-acquisition-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/paid-acquisition-lead/HEARTBEAT.md`

## Paid paths

- Channel proposals: `marketing/paid/channel-proposals/<channel-slug>.md`
- Weekly summaries: `marketing/paid/summaries/<YYYY-WW>.md`
- Creative briefs: `marketing/paid/briefs/<brief-slug>.md`
- Kill memos: `marketing/paid/kill-memos/<channel-slug>.md`

## Conventions

- No spend without CMO approval and Retention Analyst LTV:CAC sign-off.
- Two weeks above CAC threshold pauses the channel.
- Creative rotations every two weeks inside approved channels.
