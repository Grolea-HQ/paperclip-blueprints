---
schema: agentcompanies/v1
slug: sponsorship-rate-card
name: sponsorship-rate-card
description: 'Building and refreshing the sponsorship rate card every quarter — priced against rolling 30-day open rate, click-through, and active subscribers — so primary, secondary, and classified slots are sold against measurable inventory, not gut.'
---

# sponsorship-rate-card

*How Newsletter Press prices the three sponsorship slots inside the free issue so sponsors pay against real engagement and the CEO never has to defend a number that drifted from the data.*

## When to load this skill

- It is the first week of a new calendar quarter and the rate card is due for refresh.
- A sponsor pitches a multi-issue package and the per-issue price needs to be re-derived from current numbers.
- The Open/Click Analyst reports a sustained move in rolling 30-day open rate (±4pp over 60 days) and the rate card no longer reflects inventory.
- A new sponsor category (B2B operator vs. consumer) is being added and the niche premium needs to be set.
- The Cross-Promo Lead flags that a partner is closer to sponsor than swap — the rate card decides the conversation.

## Inputs

- Active subscriber count — defined as 90-day-engaged, not total list size. Sponsors who later audit will read by engagement, not by raw count.
- Rolling 30-day open rate, from the Open/Click Analyst's report.
- Rolling 30-day click-through rate.
- Last quarter's rate card from `sales/rate-card.md` for diff continuity.
- The niche premium table — tight verticals (B2B operators, technical builders) price 1.5–2x consumer baselines.
- The banned-sponsor list in `sales/banned-sponsors.md` — categories or specific brands we will not represent under the masthead.

## Procedure

### Phase 1 — Inputs

1. Pull active subscribers, rolling 30-day open rate, and rolling 30-day click-through from the Analytics weekly roll-up.
2. Confirm the numbers reconcile against the ESP dashboard. A 3pp variance means stop and reconcile before pricing.
3. Pick the niche multiplier. Default 1.0; B2B-operator newsletters 1.5; technical-builder newsletters 2.0; only the CEO can change this multiplier.

### Phase 2 — Slot pricing

The three slots are fixed. Their relative weights are fixed. Only the base price moves.

| Slot | Placement | Copy | Price |
|---|---|---|---|
| Primary | Top of issue, above the founder's first paragraph | 80–120 words plus link | Base price |
| Secondary | Mid-issue, between sections | 50–80 words plus link | 60% of primary |
| Classified | Bottom of issue, in a stacked list | One line plus link | 25% of primary |

Base price formula: `(active subscribers / 1,000) * open-rate-percent * niche-multiplier * $1.20`. Round to the nearest $50. This is the floor — never negotiate below it. Ceiling is base price + 25% for premium dates (e.g., the issue after a milestone, an end-of-year retrospective).

### Phase 3 — CEO approval and refresh

1. Draft the new rate card in `sales/rate-card.md` with last quarter's row preserved for diff.
2. The Sponsorship Sales Lead writes a one-paragraph rationale citing the three rolling metrics and the multiplier.
3. The Founder approves the rate card before any new pitch goes out. A rate card change shipped without CEO approval is rolled back.
4. Old quotes already in negotiation are honored at the prior rate.

## Outputs

- `sales/rate-card.md` — current quarter's rate card, rationale paragraph, effective date.
- `sales/rate-card-archive/<YYYY-QN>.md` — every prior quarter, for sponsor audits and CEO continuity.
- A one-line in the Sponsorship Sales Lead's weekly roll-up: this quarter's base price and the variance from last quarter.

## Anti-patterns

- Pricing against total list size. Sponsors pay for engagement, not for cold inboxes.
- Discounting below the floor to close a deal. The next sponsor finds out and the rate card breaks.
- Selling image-heavy ads. We sell native copy in the founder's voice; image creative is the sponsor's failure mode, not ours.
- Selling a sponsored full send. The masthead does not rent.
- Selling to politically aligned advertisers. Trust costs more than the deal.
- Setting a niche multiplier the CEO has not approved. Multipliers are pricing law in this business; they do not move on the Sponsorship Sales Lead's authority.
- Refreshing the rate card more than once a quarter. Volatility kills sponsor confidence and makes packages unsellable.

## Reference

Pair this skill with:
- `cross-promo-outreach` when a partner is closer to sponsor than swap.
- `esp-setup-substack-beehiiv-convertkit` for the segment definitions that determine "active subscriber" math.
