# SEO Writer Tools — SEO Bureau

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `seo-bureau/` (relative to import location)
- Agent home: `agents/seo-writer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/seo-writer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/seo-writer/HEARTBEAT.md`

## Conventions

- Drafts written against the brief's structure, angle, and internal-link map.
- FAQ candidates flagged inline so the schema layer can mark them up.
- Drafts filed under `engagements/<client>/content/drafts/`.
- AI is research and outline support, not draft replacement.
