# SEO Lead Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/seo-lead/`
- Audits: `clients/<client-slug>/seo/audits/<YYYY-MM-DD>.md`
- Monthly plans: `clients/<client-slug>/seo/plans/<YYYY-MM>.md`
- Content briefs: `clients/<client-slug>/seo/briefs/<YYYY-MM>/`
- Query inventory: `clients/<client-slug>/seo/query-inventory.md`
- Friday roll-ups: `agents/seo-lead/memory/fridays/<YYYY-WW>.md`
- Own runtime journal: `agents/seo-lead/HEARTBEAT.md`

## Skills loaded

- `ad-account-audit` — adapted for SEO technical and content audits.
- `monthly-strategy-review` — Plan-week translation.
- `client-reporting-pack` — SEO section of monthly report.

## External services

External SEO tooling (search console, third-party SEO platforms) is accessed via each client's own accounts after the Founder wires credentials post-import. No platform credentials are stored in this package.

## Conventions

- Every monthly plan declares: technical priorities, content brief count by intent class, link-acquisition activity, reporting metrics.
- Content briefs include query, intent, audience, structure, internal-link map, success metrics.
- Friday roll-up: crawl/indexation deltas, organic traffic, top movers, risks, next-week change list.
