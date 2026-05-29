---
schema: agentcompanies/v1
slug: monthly-strategy-review
name: monthly-strategy-review
description: 'Run the Plan-week strategy session per retainer that produces the signed monthly plan channel leads execute against.'
---

# monthly-strategy-review

*How Agency Engine opens every Plan week — the 60-90 minute session that converts last cycle's signal into this cycle's plan, every retainer, every month.*

## When to load this skill

- It is the first Monday of a retainer cycle and Plan week is starting (mandatory cadence).
- A QBR finding requires a mid-quarter pivot within 48 hours of the QBR call.
- A red-status recovery plan from `churn-prevention-playbook` requires a re-planned cycle with sharper objectives.
- A new retainer is finishing onboarding (Day 12-14) and Cycle 1's plan must be drafted.
- A tier upgrade just added a new channel to scope and the next plan must integrate it.

## Inputs

- Last cycle's `clients/<client-slug>/reports/<YYYY-MM>.md` with the results-vs-plan table.
- The latest `account-health-scoring` color and rationale for the account.
- The signed SOW so scope boundaries are explicit going into the session.
- The current brand voice document from `brand-voice-capture`.
- The Account Manager's captured client-signal log since the last Plan week.
- The Analyst's latest baseline-vs-current numbers per in-scope channel.

## Procedure

The session runs 60-90 minutes. Strategist owns. Account Manager joins for the signal scan. Every in-scope channel lead contributes their headline.

1. **(15 min) Last cycle review.** Results-vs-plan table walked end-to-end. What shipped, what didn't, what we learned, what we will stop doing.
2. **(15 min) Client signal scan.** Account Manager surfaces every captured client ask, sponsor sentiment shift, and risk since the previous Plan week.
3. **(15 min) Strategy frame.** Strategist proposes this cycle's objective (one sentence) and channel mix (which channels carry which load).
4. **(20 min) Channel leads contribute.** Each in-scope channel lead drafts their plan's headline: primary deliverable, success threshold, dependencies on other channels or client-side asks.
5. **(15 min) Lock and approve.** Strategist writes the plan; CEO reviews and approves before any external send; Account Manager prepares the client cover note.

### Plan document required sections

- **Cycle objective** (one sentence; must ladder to the SOW 12-month objective).
- **Channel mix** (which channels are active, primary vs. support roles).
- **Per-channel deliverables** (named, quantified, calendar-anchored).
- **Success thresholds** (the numbers `client-reporting-pack` will measure against — no plan without thresholds).
- **Run-week schedule** (which deliverable ships which week).
- **Dependencies** (client-side asks, cross-channel handoffs).
- **Risk register** (one paragraph; what could derail the cycle).

## Outputs

- `clients/<client-slug>/plans/<YYYY-MM>.md` — the signed monthly plan with all seven sections complete.
- Per-channel Run-week task queues, created by the Project Manager from the plan within 48h.
- A client-facing one-page cover note delivered by the Account Manager before Run week begins.
- A "dependencies" block forwarded to the client as the cycle's client-side ask list.
- Inputs for next month's `client-reporting-pack` results-vs-plan table already locked.

## Anti-patterns

- Plans without success thresholds — the report then has nothing to measure against and the renewal conversation has no ground to stand on.
- Plans that contradict the signed SOW silently — every contradiction must surface as a change order, not as a fait accompli.
- Plans that add scope without a `scope-creep-recovery` conversation upstream.
- Skipping the client signal scan because "nothing has changed" — the Account Manager always has signal worth surfacing.
- Letting channel leads draft headlines without dependency declaration — handoffs then break in Run week.
- Approving the plan without CEO review when external-facing deliverables are involved.

## Reference

Pair this skill with:
- `client-reporting-pack` — measures the cycle's plan with results-vs-plan.
- `scope-of-work-builder` — the boundary the plan must respect.
- `quarterly-business-review-templates` — the QBR rolls three monthly plans into a quarter narrative.
