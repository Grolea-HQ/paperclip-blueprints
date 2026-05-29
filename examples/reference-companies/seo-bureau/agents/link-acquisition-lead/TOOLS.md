# Link Acquisition Lead Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/link-acquisition-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/link-acquisition-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/link-acquisition-lead/HEARTBEAT.md`

## External services

### Link tooling (Ahrefs / Majestic / equivalent)
- **Purpose:** Prospect qualification, link profile audits, anchor distribution analysis.
- **Access:** Per-engagement project setup.
- **Convention:** Every source manually smell-tested before it joins the approved list.

### Outreach tooling (Pitchbox / BuzzStream / equivalent)
- **Purpose:** Outreach cadence management, reply tracking, placement logging.
- **Access:** Per-engagement project setup.
- **Convention:** Sequences cap at 3 touches.

## Conventions

- No outreach before CEO approves the campaign brief.
- Weekly link-velocity readout to the CEO every Friday 16:00.
- Closeout reports filed under `engagements/<client>/links/campaigns/`.
