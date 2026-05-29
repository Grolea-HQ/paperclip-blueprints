---
schema: agentcompanies/v1
slug: annual-vs-monthly-pricing-strategy
name: annual-vs-monthly-pricing-strategy
description: 'How Membership Stack anchors annual at ten-months-for-twelve, decides when to push the annual upgrade versus when to stay silent, and protects the price floor through approved launch windows only.'
---

# annual-vs-monthly-pricing-strategy

*How we run the two-tier subscription so annual carries retention and monthly carries discovery — without training members to wait for a discount.*

## When to load this skill

- The CMO is drafting an annual upsell campaign or a launch-window promo.
- A member hits day 30 of monthly and the upsell trigger fires.
- A member opens their third asset of the calendar month and qualifies for a soft annual prompt.
- An approved launch window is opening and the anchor price needs restating.
- The Founder is reviewing a request to change the anchor itself (a real pricing change, not a campaign).

## Inputs

- Current monthly and annual list prices and the price-lock cohort table.
- The member's lifecycle stage (onboarding, day 30+, post-renewal, in churn-save flow).
- Approved launch-window calendar from the Retention Analyst.
- Latest churn band and MRR additions trend — annual pushes pause when the churn band is breached.

## Procedure

1. **Confirm the anchor.** Annual is priced at ten months for twelve — the standard "two months free" framing. We do not discount deeper than that on annual outside of an approved launch window.
2. **Check the member's eligibility window.** Push annual at: day 30 of monthly, after a member's third asset open in a single calendar month, or at the start of an approved launch window. Outside those triggers, do not push annual.
3. **Apply the silence rules.** Do NOT push annual during onboarding (first 14 days), after a failed renewal attempt (churn-save flow runs first; annual upsell paused), or inside a support thread where the member is asking for help with an asset.
4. **Frame what annual buys.** Price lock, early access to any open lifetime-deal window, and a quarterly bonus asset shipped to annual members one week ahead of monthly members.
5. **State the limits.** No "annual-only library tier" — every plan accesses the full library. No money-back guarantee beyond the standard 14-day refund. No custom assets built for individual annual members.
6. **Route approvals.** Upsell copy: CEO approves. The anchor price itself: Founder approves. Launch-window pricing exceptions: Founder approves on Retention Analyst recommendation.

## Pricing decision matrix

| Member state | Push annual? | Owner |
|---|---|---|
| Days 1–14 (onboarding) | No | Member Success Lead |
| Day 30+ on monthly, churn band healthy | Yes | CMO |
| 3rd asset open in calendar month | Yes (soft prompt) | Platform Engineer trigger |
| Failed renewal, in churn-save | No — pause | Member Success Lead |
| Approved launch window open | Yes | CMO |
| Support thread active | No | Member Success Lead |

## Outputs

- `library/_marketing/annual-upsell-<campaign-slug>.md` with copy, target segment, trigger conditions, and the price points used.
- A flagged entry in the Retention Analyst's weekly cohort report under "annual conversions by trigger" so we know which trigger is carrying the load.
- A price-lock record in the billing system for every member who converts mid-cycle.

## Anti-patterns

- Discounting annual below the ten-months-for-twelve anchor outside an approved window — once we move the floor, the floor moves permanently.
- Stacking an annual upsell on top of a churn-save email — we never train members that complaining produces a discount.
- Promising "annual-only" assets — the library is one library; every plan reads it.
- Pushing annual in onboarding before the member has opened their first asset.
- Letting marketing change the anchor copy without CEO sign-off, or the anchor price without Founder sign-off.
- Treating the lifetime deal window as a permanent third tier instead of a modeled, capped exception.

## Reference

Pair this skill with:
- `lifetime-deal-vs-subscription-modeling` for window pricing math.
- `churn-save-email-flow` for the no-upsell silence rule during recovery.
