---
schema: agentcompanies/v1
slug: lifetime-deal-vs-subscription-modeling
name: lifetime-deal-vs-subscription-modeling
description: 'How the Retention Analyst models a lifetime deal window against expected subscription LTV before recommending the Founder open it — pricing it, capping it, and protecting MRR from a one-time cash bet that cannibalizes recurring revenue.'
---

# lifetime-deal-vs-subscription-modeling

*A lifetime deal is a bet that today's cash beats tomorrow's MRR additions. Model it, cap it, or do not open the window.*

## When to load this skill

- A library milestone is approaching (50 / 100 / 250 assets) and a launch window is on the table.
- A new pillar is shipping and the CMO proposes anchoring it with an LTD window.
- A seasonal revenue dip is closing in and the Retention Analyst is asked whether an LTD window can bridge it.
- The Founder is reviewing an open LTD-window proposal.
- An existing LTD cohort's support load is rising and the model needs a fresh sensitivity check.

## Inputs

- Current paying members, plan mix, and the trailing-90-day MRR trend.
- Weighted average monthly subscription price (across monthly and annualized-to-monthly).
- Trailing-12-month churn percentage and the current churn band.
- Modeled LTV per current member (current price × tenure curve at current churn).
- Proposed LTD price, the unit cap under consideration, and the expected sell-through.
- Expected per-LTD-buyer cost of service: support load, infra share, future asset cost.

## Procedure

1. **State the base equation.** For each candidate LTD price:
   - Expected LTD-buyer recurring LTV = price × 1/churn (the recurring revenue they would have generated).
   - Cost of servicing LTD buyers in perpetuity (support, infra share, future asset build).
   - **Net = LTD price − cost of servicing − cannibalized recurring LTV.**
   - If Net is negative at the expected sale volume, the window does not open.
2. **Set the unit cap before opening.** Every window has a hard cap on units sold, set BEFORE launch. The cap is never raised mid-window. Sold-out is sold-out.
3. **Define what the LTD buyer gets and doesn't get.** Gets: every current and future asset, monthly billing waived. Does NOT get: future paid pillars (if we ever ship one), affiliate payouts on their referrals, custom support tier.
4. **Run the sensitivity grid.** What happens to Net if churn rises 2 / 4 / 6 percentage points? If the sensitivity shows Net flipping negative at any plausible churn move, reduce the cap or raise the price until it doesn't.
5. **File the modeling worksheet.** Lives at `analytics/lifetime-deal-model-<window-slug>.md`. The Retention Analyst owns the file; the Founder approves the window on the Retention Analyst's recommendation.
6. **Operate the window.** CMO + Billing Specialist run the launch. Affiliate payouts are excluded on LTD referrals (see affiliate-program-setup). Annual upsell is paused for active LTD buyers (they are already paid up).

## Outputs

- `analytics/lifetime-deal-model-<window-slug>.md` — the full worksheet, versioned per window.
- A Founder-facing one-page recommendation: open / do not open, at what price, at what cap.
- A post-window readout once the window closes: units sold, cash collected, support-load delta, churn-band impact.

## Anti-patterns

- Raising the unit cap mid-window because sales are strong — every cap is set against a model, and raising it invalidates the model.
- Pricing the LTD as "two years of monthly" — that ignores the perpetual cost of servicing and the cannibalized recurring LTV from buyers who would have stayed monthly.
- Opening a window without a sensitivity check on churn — a 2-point churn move can flip a profitable window into a money-loser.
- Treating LTD as the default offer — it is a modeled, capped exception. The subscription is the only contract.
- Paying affiliate commissions on LTD referrals — the LTD price already prices the buyer; a commission on top makes the window unprofitable.
- Promising LTD buyers future paid pillars or custom support — scope creep on perpetuity tiers is how LTD cohorts go from asset to liability.

## Reference

Pair this skill with:
- `annual-vs-monthly-pricing-strategy` for how the LTD window relates to the standard anchor.
- `affiliate-program-setup` for why affiliate payouts are excluded on LTD referrals.
