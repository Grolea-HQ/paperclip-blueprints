---
schema: agentcompanies/v1
slug: paid-tier-conversion-funnel
name: paid-tier-conversion-funnel
description: 'Instrumenting and improving the path from free signup through welcome sequence to trial to paid subscriber — one stage, one change, one cohort at a time, so the conversion signal stays readable.'
---

# paid-tier-conversion-funnel

*How Newsletter Press improves free-to-paid conversion without breaking the signal — one stage, one change, one cohort at a time.*

## When to load this skill

- The Paid Tier Manager is running the weekly paid-loop review on Friday.
- Free-to-trial conversion drops below 2.0% for two consecutive weeks.
- The Cohort Churn Analyst flags a Day-30 leak that points back to the welcome sequence.
- The CEO is debating a price change and the funnel's current numbers must precede the decision.
- The Growth Lead is comparing channels by CAC-to-paid-LTV and needs the trial-to-paid conversion baseline.
- A new welcome-sequence variant is being authored and the funnel instrumentation must be in place before send.

## Inputs

- ESP exports for new free signups, welcome-sequence opens and clicks, trial starts, trial conversions, and Day-90 paid retention.
- The current welcome sequence draft from `welcome-sequence-authoring`.
- The cohort retention table from `cohort-churn-tracking`.
- The subject-line log — soft-pitch and direct-CTA emails are A/B candidates and their wins feed back here.
- The price-point sheet in `operations/esp/config.md`.

## Procedure

### The funnel — single source of truth

```
Free signup
    -> Welcome sequence (5 emails over 14 days)
    -> First free issue (soft pitch in footer)
    -> Paid offer email (day 14, direct CTA)
    -> Trial start (14-day free trial of paid tier)
    -> Trial converted to paid
    -> Paid retained at 90 days
```

### Numbers to hold the line on

| Stage | Metric | Target | Owner |
|---|---|---|---|
| Free → trial | New free subs starting trial within 30 days | 2.5% | Paid Tier Manager |
| Trial → paid | Trial conversion rate | 60% | Paid Tier Manager |
| Paid → retained | Day-90 retention | 80% | Churn Analyst |
| Paid LTV | Monthly plan / annual plan | 18 mo / 28 mo | CEO |

### One-change rule

1. **Find the worst stage by absolute conversion percentage.** Not by the gap to target — by raw conversion rate. The worst stage is where every other change is downstream noise.
2. **Pull the last 200 cohort drop-off events.** Read the welcome / pitch / trial copy at the drop point. Read it on a phone, in a Gmail preview pane, the way subscribers read it.
3. **Propose ONE change.** Copy, timing, or CTA. Never two at once, never two stages at once. The signal does not recover if you change two things.
4. **Ship.** Through the Newsletter Producer, in the same ESP, under the same sending domain.
5. **Wait 200 more events.** Not seven days — 200 events. Cadence determines the window.
6. **Measure against the prior cohort.** Lift in conversion percentage, with a one-line note on the change. Log to `analytics/funnel-changes.md`.
7. **Move to the next worst stage only after the change has landed and stabilized.** Two consecutive measurement windows.

### Escalation

Pricing changes always escalate to the CEO before ship. Copy changes inside the welcome sequence do not — the Paid Tier Manager owns them, with Managing Editor voice review.

## Outputs

- `analytics/funnel-snapshot.md` — current numbers per stage, refreshed weekly.
- `analytics/funnel-changes.md` — append-only log: date, stage, change, prior conversion, new conversion, lift, retained-or-rolled-back decision.
- A weekly one-line into the Paid Tier Manager's roll-up: which stage was worked, what changed, what lifted.

## Anti-patterns

- Changing two stages in the same cycle. We never recover the attribution.
- Running an A/B test against the paid tier. Paid subscribers expect consistency; we test on the free-to-paid path only.
- Reading week-over-week instead of event-over-event. A holiday week distorts seven-day windows.
- Proposing a price change against gut. Pricing only changes against `cohort-churn-tracking` plus the current funnel snapshot.
- Sweeping welcome-sequence copy quarterly without measuring per change. Then the entire sequence's lift is unattributable and the next rewrite has no ground truth.
- Letting the Paid Tier Manager ship copy that has not passed Managing Editor voice review. The funnel's biggest conversion lever is voice, not CTA color.

## Reference

Pair this skill with:
- `welcome-sequence-authoring` — the copy this funnel measures.
- `cohort-churn-tracking` — the downstream truth check on every funnel change.
- `subject-line-ab-testing` — the upstream open-rate driver that feeds the funnel.
