---
schema: agentcompanies/v1
slug: client-onboarding-sequence
name: client-onboarding-sequence
description: 'Run the 14-day onboarding sequence that turns a signed SOW into a Plan-week-ready Agency Engine retainer.'
---

# client-onboarding-sequence

*How Agency Engine turns a signed SOW into a Plan-week-ready retainer in 14 days — the sequence that decides whether Cycle 1 lands or limps.*

## When to load this skill

- A new SOW has been counter-signed by the client and the first month is paid.
- A retainer has upgraded tier and a new channel needs the audit-and-baseline treatment.
- A retainer has been paused and is restarting after > 60 days, requiring a re-onboarding.
- A retainer sponsor has changed mid-engagement and the kickoff narrative needs to be re-run.
- The Account Manager flags an onboarding stall (Day 7 with no audit kickoff, Day 10 with no voice session) and the sequence must be re-anchored.

## Inputs

- The counter-signed SOW from `scope-of-work-builder`.
- First month's payment confirmation from Finance Controller.
- Channel access credentials being collected by the Project Manager.
- A Day-2 kickoff call slot with the client decision-maker, CEO, and Strategist.
- The standard onboarding checklist (see Procedure) instantiated for the client.

## Procedure

1. **Day 1 — SOW counter-sign and welcome.** Account Manager sends the welcome email with kickoff brief, calendar links, and the access-request list (channels, analytics, ad accounts, email platform).
2. **Day 2-3 — Kickoff call.** Account Manager, CEO, and Strategist on the call with client decision-maker. Inputs captured: business model, 12-month objective, channel access status, success metrics, internal stakeholders.
3. **Day 4-7 — Brand voice capture.** Creative Director runs `brand-voice-capture`; document drafted within 48h of session.
4. **Day 4-10 — Channel audits in flight.** Each in-scope channel lead runs `ad-account-audit`; Analyst sets the analytics baseline in parallel.
5. **Day 10-12 — Discovery brief.** Strategist consolidates audits, voice document, and kickoff notes into a discovery brief reviewed by the CEO.
6. **Day 12-14 — First monthly plan.** Strategist runs `monthly-strategy-review` for Cycle 1; CEO approves before external send; Account Manager delivers to client.
7. **Day 14 — Cycle 1 Run week begins.** Project Manager converts the plan into Run-week task queues; Plan → Run → Report rhythm is now active.

### Onboarding deliverables checklist

- Counter-signed SOW filed at `clients/<client-slug>/sow/<signed-date>.md`.
- Discovery brief at `clients/<client-slug>/strategy/discovery-brief.md`.
- Brand voice document at `clients/<client-slug>/brand/voice-v1.md`.
- Per-channel audit reports at `clients/<client-slug>/audits/<channel>-<YYYY-MM>.md`.
- Analytics baseline at `clients/<client-slug>/baselines/analytics-<YYYY-MM>.md`.
- Cycle 1 monthly plan at `clients/<client-slug>/plans/<YYYY-MM>.md`.
- Day-30 first health score scheduled for the next Monday `account-health-scoring` sweep.

## Outputs

- A retainer that lands its first Plan → Run → Report cycle on cadence with zero ambiguity about scope, voice, or baseline.
- A complete onboarding folder structure under `clients/<client-slug>/` ready for Run-week execution.
- A Day-30 first formal health score on the books, anchoring the retention curve.
- A Cycle 1 monthly plan the client has signed off on before Run-week begins.

## Anti-patterns

- Skipping channel audits to "move fast" — the first month's plan then lands on assumptions, not data.
- Starting Run week before audits and the brand voice document are captured (creative drift is locked in from Cycle 1).
- Onboarding without the Day-2 kickoff call — the Strategist drafts the discovery brief from second-hand notes and misses the sponsor's actual priorities.
- Letting the Day-12 plan slip past Day 14 — Run week then starts late and Cycle 1 reports show a 3-week month, ugly versus a clean baseline.
- Running onboarding without the CEO on the kickoff call — sponsor trust is built on the kickoff, and recovery later is expensive.
- Treating Day 30 as a soft milestone — the first health score must be filed; it sets the retention narrative.

## Reference

Pair this skill with:
- `ad-account-audit` for the Day-4-10 per-channel work.
- `brand-voice-capture` for the Day-4-7 voice session.
- `monthly-strategy-review` for the Day-12-14 Cycle 1 plan.
- `account-health-scoring` for the Day-30 first score.
