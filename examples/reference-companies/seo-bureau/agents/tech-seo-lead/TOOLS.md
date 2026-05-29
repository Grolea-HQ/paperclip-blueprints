# Tech SEO Lead Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/tech-seo-lead/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/tech-seo-lead/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/tech-seo-lead/HEARTBEAT.md`

## External services

### Google Search Console
- **Purpose:** Indexation, coverage, Core Web Vitals field data, manual actions, rich-results performance.
- **Access:** Per-client OAuth granted during onboarding.
- **Convention:** Pull baseline numbers on day 10 of onboarding.

### Crawl tooling (Screaming Frog / Sitebulb / equivalent)
- **Purpose:** Crawl, render, internal-link, redirect, hreflang audits.
- **Access:** Local CLI / desktop license.
- **Convention:** Always run with JS rendering enabled for audit-tier engagements.

## Conventions

- Audit decks ship through the audit template. Off-template decks go back.
- Schema plans bind to CMS fields, not hardcoded JSON-LD.
- Recovery sprints follow the algorithm-recovery-protocol skill end-to-end.
