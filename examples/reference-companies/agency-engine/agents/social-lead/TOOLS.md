# Social Lead Tools — Agency Engine

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Agent home: `agents/social-lead/`
- Audits: `clients/<client-slug>/social/audits/<YYYY-MM-DD>.md`
- Monthly plans + calendars: `clients/<client-slug>/social/plans/<YYYY-MM>.md`
- Pillar inventory: `clients/<client-slug>/social/pillars.md`
- Friday roll-ups: `agents/social-lead/memory/fridays/<YYYY-WW>.md`
- Own runtime journal: `agents/social-lead/HEARTBEAT.md`

## Skills loaded

- `monthly-strategy-review` — Plan-week translation to social plan and calendar.
- `client-reporting-pack` — social section of monthly report.
- `brand-voice-capture` — caption voice anchored in captured client voice.

## External services

Social platform access (Meta, LinkedIn, TikTok, X, YouTube, etc.) routes through each client's own accounts after the Founder wires credentials post-import. No social credentials are stored in this package.

## Conventions

- Every monthly plan declares: content pillars, post count per pillar, format mix, voice anchors, success thresholds.
- Friday roll-up format: posts shipped, primary engagement metric, audience growth, deltas vs. plan, next-week changes.
- Crisis comms protocol: stop posting, flag CEO, draft response, await CEO approval before sending.
