# Video Producer Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/video-producer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/video-producer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/video-producer/HEARTBEAT.md`

## Video paths

- Walkthroughs: `library/videos/<category>/<video-slug>/`
- Short-form clips: `content/clips/<release-slug>/`
- Recording notes: `content/video-notes/<video-slug>.md`

## Conventions

- Friday hand-off for Week-4 walkthroughs.
- Cross-check asset version against the live library before recording.
- Annual refresh window for out-of-date walkthroughs; no ad-hoc re-records.
