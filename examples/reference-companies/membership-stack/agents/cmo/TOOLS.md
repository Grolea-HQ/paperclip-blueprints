# CMO Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/cmo/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/cmo/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/cmo/HEARTBEAT.md`

## Marketing paths

- Landing page copy: `marketing/landing-pricing.md`, `marketing/landing-hero.md`
- Pricing decision memo: `marketing/pricing-memo.md`
- Affiliate program page: `marketing/affiliate-program.md`
- Email blasts: `marketing/emails/blasts/`
- Social copy log: `marketing/social-log.md`

## Conventions

- Pricing changes routed to CEO → Founder.
- Above-tier affiliate payouts routed to Founder.
- Every external surface reviewed for the three identity distinctions before publish.
