# Market Researcher Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/market-researcher/`
- Competitive briefs: `clients/<client-slug>/research/competitive-<YYYY-Q>.md`
- Audit findings: `clients/<client-slug>/research/audits/<channel>-<YYYY-MM-DD>.md`
- Running watchlist: `agents/market-researcher/memory/watchlists/<client-slug>.md`
- Own runtime journal: `agents/market-researcher/HEARTBEAT.md`

## Skills loaded

- `brand-voice-capture` — voice research from competitor and audience review.
- `ad-account-audit` — paid audit framework.

## Conventions

- Every claim cites its source (URL, platform, date pulled).
- Briefs structured as: question, evidence, implication, recommended next step for Strategist.
- Audit findings are written with the channel lead's vocabulary (CPM, ROAS, CTR for paid; coverage, depth, intent for SEO).
