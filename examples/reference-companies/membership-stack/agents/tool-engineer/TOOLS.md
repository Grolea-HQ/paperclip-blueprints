# Tool Engineer Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/tool-engineer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/tool-engineer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/tool-engineer/HEARTBEAT.md`

## Approved managed hosts

- Vercel (static + serverless).
- Google Apps Script (Sheets / Docs-tied tools).
- Notion (template-as-tool surfaces).
- Cloudflare Pages (static).

## Version control

- Branches: feature branches off `main`. Name: `tool/<short-description>`.
- Never merge into `main` yourself. Open a PR; the CEO reviews and approves merges for tool releases.
- After a PR is merged, delete the feature branch locally and remotely on your next wakeup.

## Conventions

- Tools are stateless: no member-data persistence server-side.
- Every tool has an INDEX.md, release-notes.md, and a next-refresh date in maintenance notes.
