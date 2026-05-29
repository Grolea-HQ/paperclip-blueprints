---
schema: agentcompanies/v1
slug: scope-of-work-builder
name: scope-of-work-builder
description: 'Translate an approved retainer pitch into a signed SOW that locks scope, deliverable cadence, and change-order rules.'
---

# scope-of-work-builder

*How Agency Engine converts a verbally-accepted pitch into a signed SOW — the document that defines every Plan to Run to Report cycle and grounds every scope-creep conversation.*

## When to load this skill

- A retainer pitch from `retainer-pitch-authoring` has been verbally accepted and a signed SOW must be drafted.
- The Project Manager is converting a Plan-week plan into Run-week task queues and needs the canonical scope source.
- A change order is being scoped after a `scope-creep-recovery` event and the SOW needs to be amended or referenced.
- A QBR-triggered re-tier (Foundation → Growth, Growth → Scale) is closing and a refreshed SOW is the deliverable.
- A renewal is approaching its 90-day point and the SOW needs a renewal-aware refresh before the auto-rollover date.

## Inputs

- The verbally-accepted pitch from `retainer-pitch-authoring` with tier, scope-in, scope-out, cadence, term.
- The latest tier defensibility memo from `pricing-and-proposal-templates`.
- The discovery brief from the Strategist (for context on objectives the SOW supports).
- The current Account Manager assigned to the account.
- Finance Controller for pricing sanity-check before counter-sign.

## Procedure

1. **Draft within 5 business days of verbal acceptance.** Account Manager owns the draft; CEO reviews before send.
2. **Use the eight-section structure** below — every SOW carries all eight sections, no exceptions.
3. **Name channels in scope concretely.** No "as needed" volume; every channel has a deliverable cadence (e.g., paid: 1 strategy plan + ongoing optimization, lifecycle: 4 emails + 2 flows per month).
4. **Name channels out of scope explicitly.** Anti-drift requires this; "we don't do X" must be on paper.
5. **Calendar-anchor the schedule.** Plan week (week 1), Run weeks (weeks 2-3), Report week (week 4) — not vibe.
6. **Name the change-order policy.** Per `scope-creep-recovery`. The SOW cites the policy in its own body.
7. **CEO review and client send.** No SOW goes to client without CEO sign-off.
8. **Counter-signature and filing.** Client signs; first month invoiced; SOW filed at `clients/<client-slug>/sow/<signed-date>.md`.

### SOW sections (in order)

1. **Retainer tier and pricing.** Foundation / Growth / Scale; monthly amount; term (90-day initial, monthly thereafter).
2. **Channels in scope.** Each named channel with its monthly deliverable cadence and primary KPI.
3. **Channels out of scope.** Named explicitly — anti-drift is mandatory.
4. **Plan-week, Run-week, Report-week schedule.** Calendar-anchored to the cycle.
5. **Reporting cadence.** Monthly client report delivered by Day 3 of following month; QBR within 14 days of quarter end.
6. **Approval and escalation model.** Account Manager primary contact; CEO approves external changes; Founder approves tier changes.
7. **Change-order policy.** Any out-of-scope ask becomes a written change order or a re-scope conversation; silent absorption is rejected.
8. **Term and renewal.** 90-day initial; monthly thereafter; renewal decision at QBR or 30 days before, whichever comes first.

## Outputs

- A counter-signed SOW filed at `clients/<client-slug>/sow/<signed-date>.md`.
- Run-week task queues converted by the Project Manager from the in-scope cadence within 48h of counter-sign.
- A renewal anchor document the Head of Accounts references at every QBR.
- A reference the `scope-creep-recovery` skill cites by name on every out-of-scope ask.
- A pricing line item filed with the Finance Controller for MRR roll-up.

## Anti-patterns

- "Best efforts" language without deliverable cadence — unenforceable; the client reads "best efforts" as "infinite scope".
- Unbounded "as needed" volume — every channel must have a quantified cadence.
- Project deliverables bundled into the retainer without separate accounting — pollutes retainer math; project work over $5K is its own line.
- Skipping the channels-out-of-scope section because it feels "negative" — without it, scope creep has no anchor to push against.
- Sending the SOW without CEO sign-off — every external commitment passes through the CEO gate.
- Allowing 60-day or 30-day initial terms instead of 90 — collapses LTV math; the 90-day initial is non-negotiable per `COMPANY.md`.

## Reference

Pair this skill with:
- `retainer-pitch-authoring` — the upstream pitch.
- `pricing-and-proposal-templates` — the tier definitions cited.
- `scope-creep-recovery` — the policy this SOW codifies.
- `client-onboarding-sequence` — the 14-day sequence triggered by counter-sign.
