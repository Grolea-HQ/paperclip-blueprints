# Platform Engineer Tools — Membership Stack

## Paperclip API

Load the **`paperclip` skill** for any Paperclip API interaction. It covers the full API reference, heartbeat procedure, and critical rules.

- Base URL: `http://localhost:3100/api` (or `$PAPERCLIP_API_URL`)
- Agent ID: `<set at runtime>`
- Company ID: `$PAPERCLIP_COMPANY_ID`

## File system

- Company root: `membership-stack/` (relative to import location)
- Agent home: `agents/platform-engineer/`
- Company constitution: `COMPANY.md`
- Operating manual: `OPERATIONS.md`
- Project inventory: `PROJECT-INVENTORY.md` (read before delegating any task)
- Own memory: `agents/platform-engineer/memory/` (daily notes — the `para-memory-files` skill manages this)
- Own runtime journal: `agents/platform-engineer/HEARTBEAT.md`

## Browser automation

Use the **`dev-browser`** skill for any task requiring browser interaction (billing-provider dashboard, member-portal QA, community-platform admin). Load the skill for server start commands and usage patterns.

## Platform paths

- Platform config: `platform/config/`
- Onboarding tour wiring: `platform/onboarding/`
- Email trigger plumbing: `platform/triggers/`
- Maintenance summaries: `platform/maintenance/<YYYY-MM>.md`
- Incident log: `platform/incidents/<YYYY-MM-DD>-<slug>.md`

## Version control

- Branches: feature branches off `main`. Name: `platform/<short-description>`.
- Never merge into `main` yourself. CEO reviews platform PRs; Founder approves migration-level PRs.
- After a PR is merged, delete the feature branch locally and remotely on your next wakeup.

## Conventions

- Patches inside the monthly maintenance window.
- 30-minute incident clock to CEO escalation.
- New vendor dependencies require CEO approval.
