---
schema: agentcompanies/v1
slug: scope-creep-recovery
name: scope-creep-recovery
description: 'Capture every out-of-scope client ask and convert it into a change order or a re-scope conversation — never silent absorption.'
---

# scope-creep-recovery

*How Agency Engine catches scope creep before it kills retainer math — the play the Project Manager runs every time an out-of-scope ask appears, no exceptions.*

## When to load this skill

- A client asks for a deliverable not named in the signed SOW.
- A client asks for higher cadence than the SOW specifies (e.g., weekly when the tier is monthly).
- A client asks to add a new channel mid-cycle (e.g., adding paid social to a paid-search-only retainer).
- A channel lead reports executing work outside their SOW scope (internal silent absorption — equally dangerous).
- A QBR brief surfaces a pattern of repeated silent absorptions across a quarter.

## Inputs

- The signed SOW from `scope-of-work-builder` — defines what is in scope, end of story.
- The current monthly plan from `monthly-strategy-review` for the affected cycle.
- The client ask itself (email thread, call note, Slack message — captured verbatim with timestamp).
- The Project Manager's scope-creep log for the account.
- Account Manager available within 24 hours; Head of Accounts and CEO on standby for re-scope conversations.

## Procedure

The play runs on a 48-hour clock. No out-of-scope ask sits beyond 48 hours without a decision.

1. **Capture within 4 hours.** Project Manager logs the ask in `clients/<client-slug>/scope-log/<YYYY-MM>.md`: source, deliverable, date, in-scope ruling (pending), proposed change order amount.
2. **Triage within 24 hours.** Account Manager confirms in-scope vs. out-of-scope by reading the SOW; Project Manager confirms the effort cost in roster hours.
3. **Decide within 48 hours.** One of three paths:
   - **In-scope** → Document the precedent in the log; proceed.
   - **Change order** → Account Manager drafts a written change order with price and timeline within 48h; client approves before work begins.
   - **Re-scope conversation** → Head of Accounts and CEO host a re-tier conversation (Foundation → Growth, or scope reduction, or pricing change).
4. **Communicate to the client.** Account Manager replies in writing within 48h: "We've captured this. Here is the change order / here is the re-scope path we're proposing."
5. **Update the SOW or change-order log.** No verbal change is ever in scope by default; the written record is the contract.
6. **Trend-watch.** Project Manager flags the account to `account-health-scoring` if three+ asks land in a single month — pattern indicates a tier mismatch.

### Decision matrix

| Trigger | Default path | Owner | Time-to-decision |
|---|---|---|---|
| Single small ask, low effort | Change order | Account Manager | 48h |
| Repeated asks (3+ in a month) | Re-scope / re-tier conversation | Head of Accounts + CEO | 5 business days |
| New channel request | Re-scope conversation; new audit required | CEO | 5 business days |
| Higher cadence request | Re-tier conversation | Head of Accounts + CEO | 5 business days |
| Internal silent absorption flagged | Channel lead stops work; PM logs; re-scope or change order | Project Manager | 24h |

## Outputs

- A scope-log entry at `clients/<client-slug>/scope-log/<YYYY-MM>.md` per ask, with decision and date.
- A written change order at `clients/<client-slug>/change-orders/<YYYY-MM-DD>.md` for the change-order path.
- A re-scope memo at `clients/<client-slug>/strategy/rescope-<YYYY-MM-DD>.md` for the re-scope path.
- A pattern flag to `account-health-scoring` when repeat absorption is detected.
- A refreshed SOW from `scope-of-work-builder` when a re-tier conversation closes.

## Anti-patterns

- Silent absorption — the single most common scope-creep failure mode; the channel lead "just does it" and the retainer math erodes invisibly.
- Verbal change orders — every change is written; verbal becomes "I never agreed to that" at QBR.
- Letting an out-of-scope ask sit beyond 48 hours — the client perceives ambiguity as agreement.
- Trading scope for renewal odds without CEO sign-off — destroys retainer math to chase a renewal that was likely anyway.
- Treating a single ask as the whole story — the trend across a month matters more than any individual ask.
- Account Managers giving away work to keep a client "happy" — short-term harmony, long-term margin death.

## Reference

Pair this skill with:
- `scope-of-work-builder` — the SOW being enforced.
- `account-health-scoring` — the place where repeated absorption surfaces as scope-discipline red.
- `churn-prevention-playbook` — when absorption has already driven a red status.
