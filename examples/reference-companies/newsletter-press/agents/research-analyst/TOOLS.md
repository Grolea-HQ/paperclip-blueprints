# Research Analyst Tools — Newsletter Press

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `newsletter-press/`
- Agent home: `agents/research-analyst/`
- Fact-check folder: `editorial/fact-check/<issue-date>.md` — one file per issue.
- Niche-data file: `editorial/research/niche-data.md` — standing reference, updated monthly.
- Citations workspace: `editorial/citations/` — shared with Staff Writer.
- Voice guide: `editorial/voice-guide.md` (read for context, not editing).
- Project inventory: `PROJECT-INVENTORY.md`.
- Own memory: `agents/research-analyst/memory/`.

## Browser automation

Use the **`dev-browser`** skill for any task requiring browser interaction with primary-source pages (government data portals, regulator filings, academic archives) where a static fetch is not enough.

## Conventions

- Every fact-check entry has: claim, source, retrieved-on date, primary/secondary flag, verdict.
- I never edit a claim — I return a verdict to the Managing Editor.
- I run a link-rot audit on the niche-data file the first Monday of every quarter.
