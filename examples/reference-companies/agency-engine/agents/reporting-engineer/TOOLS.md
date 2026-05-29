# Reporting Engineer Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/reporting-engineer/`
- Report templates: `clients/<client-slug>/reports/template.md`
- Monthly reports: `clients/<client-slug>/reports/<YYYY-MM>.md`
- QBR data packs: `clients/<client-slug>/reports/qbr/<YYYY-Q>.md`
- QA log: `agents/reporting-engineer/memory/qa/<YYYY-MM>.md`
- Own runtime journal: `agents/reporting-engineer/HEARTBEAT.md`

## Skills loaded

- `client-reporting-pack` — assembly framework, section structure, QA checklist.
- `creative-qa-pipeline` — QA discipline applied to report packs.

## Conventions

- Every report pulls only from data-quality-signed datasets.
- Template includes: executive summary, channel-by-channel, results-vs-plan, next-cycle preview.
- QA checklist confirmed in the QA log before handoff to Account Manager.
