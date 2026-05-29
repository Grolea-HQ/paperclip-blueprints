# Product Manager Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/product-manager/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/product-manager/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/product-manager/HEARTBEAT.md`

## Asset library paths

- Library root: `library/`
- Templates: `library/templates/<category>/<asset-slug>/`
- Tools: `library/tools/<category>/<tool-slug>/`
- Guides: `library/guides/<category>/<guide-slug>/`
- Videos: `library/videos/<category>/<video-slug>/`
- Taxonomy: `library/taxonomy.md`
- Deprecated: `library/_deprecated/`

## Conventions

- Every asset folder contains INDEX.md and release-notes.md.
- New tags require CEO approval before added to taxonomy.
