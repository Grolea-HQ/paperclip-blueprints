# Digital PR Specialist Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/digital-pr-specialist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/digital-pr-specialist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/digital-pr-specialist/HEARTBEAT.md`

## External services

### Journalist research tooling (Muck Rack / Roxhill / equivalent)
- **Purpose:** Real recent coverage research, journalist beat verification, contact validation.
- **Access:** Per-engagement project setup.
- **Convention:** No "PR contact" databases; every journalist is verified by recent coverage.

### Outreach tooling (Pitchbox / BuzzStream / equivalent)
- **Purpose:** Send cadence, reply tracking, follow-up management.
- **Access:** Per-engagement project setup.
- **Convention:** One follow-up max per pitch.

## Conventions

- Pitches drafted per the digital-pr-pitch-writing skill.
- Placement reports filed under `engagements/<client>/links/pr/`.
- No pitch sent without Link Acquisition Lead sign-off.
