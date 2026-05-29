---
schema: agentcompanies/v1
slug: churn-save-email-flow
name: churn-save-email-flow
description: 'The three trigger-specific email sequences (failed renewal, cancel-button click, confirmed cancel) the Member Success Lead runs to recover MRR without sounding desperate or training members to churn to get a discount.'
---

# churn-save-email-flow

*A failed renewal is a payment problem half the time. We solve the payment problem first and the relationship problem second — and we never offer a discount to slow churn.*

## When to load this skill

- A renewal charge fails (card declined, auth lapsed, billing details expired).
- A member clicks the cancel button but has not yet confirmed.
- A member confirms cancellation and the post-cancel sequence opens.
- The Retention Analyst's cohort review surfaces a sequence-A or sequence-C pattern that needs copy revision.
- The Billing Specialist flags a failed-renewal volume spike (more than usual) and we need to confirm the sequence is firing.

## Inputs

- The billing event payload from the Billing Specialist (which trigger fired, when, member tenure, plan).
- The member's first-name and tenure on file.
- The current library count and last three assets shipped — used in the day-30 winback email after a confirmed cancel.
- The cancel reason (if captured) for the Retention Analyst log.

## Procedure

The three sequences never overlap. Trigger A runs only until either resolved or escalated into Trigger C.

### Sequence A — Failed renewal (3 emails over 7 days)

1. **Day 0** — "Your card didn't go through — here's the update link." Plain. No upsell. Signed by Member Success Lead.
2. **Day 3** — "Still seeing the failed charge. Want me to switch you to a different card? Reply with 'switch'." Personal, named, single ask.
3. **Day 6** — "If we don't hear back today, your access pauses tomorrow. Here's the link." No drama, no discount.

### Sequence B — Cancel button clicked, not yet confirmed (1 email)

- **Immediate** — "Saw you opened the cancel flow. Before you confirm: what asset were you looking for that we didn't have?" Reply routes to Member Success Lead.

### Sequence C — Confirmed cancel (2 emails)

1. **Day 0** — "You're cancelled. Here's how to re-export anything you saved. No hard feelings." One-question survey: why?
2. **Day 30** — "Library shipped X, Y, Z since you left. Door's open if you want back in." One offer (current standard pricing), no urgency, no discount.

## Outputs

- `library/_marketing/churn-save/<sequence>-<version>.md` — copy, trigger conditions, owner sign-offs.
- A row per send in `analytics/churn-save-log.md` for the Retention Analyst's cohort review.
- A cancel-reason entry for every confirmed cancel, used to detect the 5-in-30-days pattern threshold that triggers a positioning review.
- A weekly delta into "churn %" and "MRR recovered from failed renewals" for the cohort report.

## Anti-patterns

- Offering a discount to save a churn — we do not train members to churn to get a discount. Once the precedent exists, it cannot be undone.
- Mixing the annual upsell into sequence A — the churn-save flow pauses every upsell; recovery comes first.
- Sending sequence-A emails from a no-reply address — every email is from a named human (Member Success Lead) at a monitored inbox.
- Stacking sequences (A and C running concurrently) — when sequence A escalates to a confirmed cancel, sequence A stops and sequence C opens.
- Skipping the day-30 winback because "they already cancelled" — the back catalogue compounds, and a member who left at asset 30 is a different prospect at asset 50.
- Treating the cancel survey as optional — without it the Retention Analyst can't surface library gaps or positioning drift.

## Reference

Pair this skill with:
- `member-survey-protocol` for the cancel-reason single-question and the quarterly readout.
- `annual-vs-monthly-pricing-strategy` for why no annual upsell runs inside the churn-save flow.
