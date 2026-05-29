# Digital PR Lead Tools — Niche Site Empire

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `niche-site-empire/` (relative to import location)
- Agent home: `agents/digital-pr-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/digital-pr-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/digital-pr-lead/HEARTBEAT.md`

## External services

Common tools referenced generically — HARO / Connectively / Qwoted query monitors, media contact databases, press-release distribution. Access via the Portfolio Owner's accounts.

## Conventions

- HARO sweep happens at 08:00 / 13:00 / 17:00 weekdays — three sweeps daily, no exceptions.
- Daily HARO pitch log lives at `portfolio/digital-pr/haro-log-<date>.md`.
- Press releases for digital PR campaigns live under each campaign's folder.
