---
schema: agentcompanies/v1
slug: cohort-churn-tracking
name: cohort-churn-tracking
description: 'Rebuilding the paid-tier cohort retention table every month so we can distinguish an onboarding leak from a value problem from a coverage-exhaustion problem before we change price or copy.'
---

# cohort-churn-tracking

*How we read paid-tier churn at Newsletter Press so a Day-30 leak never gets misdiagnosed as a Day-90 value problem — and vice versa.*

## When to load this skill

- It is the first Monday of the month and the Churn Analyst owes the CEO a refreshed cohort table.
- The Paid Tier Manager is proposing a price-point or offer change and needs to pressure-test the diagnosis.
- A welcome-sequence rewrite is being considered and the Day-30 retention curve is the gating evidence.
- The CEO is asked by a sponsor or partner what our paid-tier retention actually is.
- Trial-to-paid conversion drops two months in a row — the table tells us whether the leak is upstream (trial copy) or downstream (Day-30 onboarding).

## Inputs

- Subscription start and cancellation events from the ESP (Substack Stripe export, beehiiv Premium export, or ConvertKit Commerce subscription log).
- The trial-to-paid log from `paid-tier-conversion-funnel` so trial-converted starts can be flagged separately from direct-paid starts.
- Last month's `analytics/cohort-table.md` for diff continuity.
- The send cadence log — a missed send week distorts the next cohort's first 30 days.

## Procedure

1. **Define the cohort.** A cohort is every paid subscriber who started in the same calendar month, regardless of monthly vs. annual. Annuals are tracked separately in a parallel sheet so a 12-month commitment does not mask monthly churn.
2. **Pull the events.** Export from the ESP. Cross-check totals against the last revenue line — counts must reconcile to the dollar.
3. **Compute Day-30, Day-60, Day-90, Day-365 retention.** Day-N retention = (cohort members still paying on Day N) / (cohort size). Cancellations queued for end-of-period count as cancelled the day they queue, not the day they expire.
4. **Apply the diagnostic ladder.** This is the load-bearing step:

| Pattern | Diagnosis | Owner of the fix |
|---|---|---|
| Day-30 retention < 90% | Onboarding leak — first paid email or trial-to-paid handoff is failing | Paid Tier Manager (welcome sequence + first-week paid issue) |
| Day-30 ≥ 90%, Day-90 < 75% | Value problem — the paid content is not delivering on the welcome promise | CEO (editorial scope of the paid tier) |
| Day-90 ≥ 75%, Day-365 < 60% | Coverage exhaustion — founder's topic surface has narrowed and long-time paid readers have read everything | CEO (editorial expansion or sunset) |
| All three healthy, MRR still flat | Acquisition problem, not churn — re-read with Growth Lead | Growth Lead |

5. **Write the report.** One page. Cohort table, the row that triggered an action, the proposed fix, and the cost of doing nothing.
6. **Publish on Monday morning, before the editorial sync.** The CEO must read it before approving any pricing or welcome-sequence change.

## Outputs

- `analytics/cohort-table.md` — the rolling 18-month cohort retention matrix, rebuilt monthly.
- `analytics/cohort-reports/<YYYY-MM>.md` — narrative report and recommended fix.
- A diff line in the Analytics weekly roll-up flagging any cohort that crossed a diagnostic threshold this month.

## Anti-patterns

- Reading "average paid retention" as a single number. Averages hide the cohort the leak lives in.
- Counting end-of-period queued cancellations as still-retained. They are not. They are dollars on the way out.
- Proposing a price change against gut feel before the table is rebuilt. Pricing only changes against this artifact.
- Including the founder's own free comp accounts as cohort members. They distort small cohorts in the first six months.
- Merging trial-converted and direct-paid starts into one cohort. They churn on different curves and the merged cohort hides which welcome-sequence variant is leaking.
- Skipping the monthly rebuild because "nothing changed." The diagnostic ladder works only on a fresh table.

## Reference

Pair this skill with:
- `paid-tier-conversion-funnel` when Day-30 retention is the failing stage.
- `audience-survey-protocol` when the table flags a value problem and we need stated reasons.
