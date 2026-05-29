# Schema Implementation Specialist Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/schema-implementation-specialist/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/schema-implementation-specialist/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/schema-implementation-specialist/HEARTBEAT.md`

## External services

### Google Search Console
- **Purpose:** Rich-results performance, structured-data error reports.
- **Access:** Per-client OAuth granted during onboarding.
- **Convention:** Rich Results report reviewed monthly during the report cycle.

### Schema validation tooling (Rich Results Test, Schema.org Validator)
- **Purpose:** Pre- and post-deployment validation.
- **Access:** Public web tools.
- **Convention:** Validation outputs filed under `engagements/<client>/technical/schema/`.

## Conventions

- High-leverage schema types only. No stuffing.
- Field-binding specs bind to CMS data, not hardcoded JSON-LD.
- Post-deployment validation is non-negotiable.
