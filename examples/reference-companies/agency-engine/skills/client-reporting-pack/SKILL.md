---
schema: agentcompanies/v1
slug: client-reporting-pack
name: client-reporting-pack
description: 'Assemble the monthly Agency Engine client report pack — the renewal-grade deliverable that closes every Plan to Run to Report cycle.'
---

# client-reporting-pack

*How Agency Engine closes every retainer cycle — the dense, honest, renewal-grade report that is the actual reason clients renew at 85%+ gross retention.*

## When to load this skill

- It is Day 1-2 of the calendar month and the previous month's retainer cycle is closing.
- A QBR is being assembled and the quarter's three monthly reports need rollup.
- An account has turned red and the Account Manager needs the last cycle's report as evidence for the recovery conversation.
- A renewal conversation is scheduled and the Head of Accounts is pulling the trailing three reports as renewal narrative.
- A mid-cycle pivot was approved and the report must reflect the changed plan, not the original.

## Inputs

- The signed monthly plan from `monthly-strategy-review` at `clients/<client-slug>/plans/<YYYY-MM>.md` — defines what success-vs-plan means.
- Channel-lead Run-week output for each in-scope channel.
- Analyst data-quality sign-off (no report ships without it).
- The previous month's report for trend continuity.
- The current SOW so out-of-scope work doesn't leak into the report.

## Procedure

1. **Day 1 — Reporting Engineer kicks off.** Pulls all channel data; flags any data-quality issues to the Analyst for resolution before assembly.
2. **Day 1 — Channel leads draft commentary.** Each in-scope channel lead writes one block: what shipped, what moved, why, what's next.
3. **Day 2 — Analyst data-quality sign-off.** No report ships without this gate. Attribution caveats explicitly named.
4. **Day 2 — Strategist drafts the next-cycle preview.** One paragraph that previews the next Plan-week direction.
5. **Day 2 — Reporting Engineer assembles the full pack** in the section order below; checks against the Plan-week success thresholds.
6. **Day 3 — Account Manager delivers** to the client by 17:00 local, with a 20-minute review call scheduled within 7 days.
7. **Day 3 — File the pack** at `clients/<client-slug>/reports/<YYYY-MM>.md` and update the Monday health sweep input for the next `account-health-scoring`.

### Report sections (in order)

1. **Executive summary.** Three sentences. What shipped, what moved, what's next.
2. **Results-vs-plan table.** Per channel: planned KPI vs. actual, with delta and one-line "why".
3. **Channel-by-channel commentary.** One block per active channel, written by the channel lead.
4. **Attribution and data quality.** Sourced from Analyst; data-quality sign-off referenced; caveats named.
5. **Wins.** Concrete, evidence-cited (no vanity).
6. **Risks and asks.** Concrete asks for the client (creative review, approvals, access, content provision).
7. **Next-cycle preview.** One paragraph from the Strategist tying back to the SOW objectives.

## Outputs

- `clients/<client-slug>/reports/<YYYY-MM>.md` — the renewal-grade monthly report, delivered to the client by Day 3.
- A results-vs-plan table that the QBR brief and the renewal conversation will both reference directly.
- A "risks and asks" block converted into next-cycle task queues by the Project Manager.
- Analyst sign-off filed in `clients/<client-slug>/reports/<YYYY-MM>-data-quality.md`.

## Anti-patterns

- Vanity metrics (raw impressions, raw clicks, follower count) without a tied-to-objective context.
- Padding short months with extra commentary — flat is flat in the report; honest beats verbose.
- Reports that omit the results-vs-plan table — the entire renewal story depends on it.
- Shipping the report without Analyst data-quality sign-off (attribution caveats then surface only at QBR, which destroys trust).
- Treating out-of-scope work as a "bonus win" in the report — it normalizes scope absorption and kills retainer math.
- Letting the report slip past Day 3 — cadence is the product; missing Day 3 is itself a churn signal.

## Reference

Pair this skill with:
- `monthly-strategy-review` — the Plan-week output this report measures against.
- `quarterly-business-review-templates` — the QBR brief rolls up three monthly reports.
- `account-health-scoring` — the Monday sweep reads the latest results-vs-plan delta.
