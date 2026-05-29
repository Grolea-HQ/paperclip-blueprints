# Content Strategist Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/content-strategist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/content-strategist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/content-strategist/HEARTBEAT.md`

## External services

### Keyword and SERP tooling (Ahrefs / Semrush / equivalent)
- **Purpose:** Keyword volume, SERP analysis, query expansion, internal-link suggestions.
- **Access:** Per-engagement project setup.
- **Convention:** Cluster plans built from real SERP analysis, not assumed intent.

## Conventions

- Briefs follow the content-brief-templates skill end-to-end.
- Cluster plans filed under `engagements/<client>/content/clusters/`.
- Editor reviews briefs before assignment to the writer.
- We brief; the client publishes.
