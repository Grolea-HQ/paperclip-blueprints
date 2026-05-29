---
schema: agentcompanies/v1
slug: affiliate-program-setup
name: affiliate-program-setup
description: 'How the Affiliate Manager screens applicants, structures the 30% recurring payout, polices promotional claims, and ships affiliates live so the channel drives 20%+ of new MRR without forcing paid acquisition to carry the load alone.'
---

# affiliate-program-setup

*How Membership Stack runs an affiliate channel that compounds MRR additions instead of training affiliates to race the payout to the bottom.*

## When to load this skill

- A new affiliate application lands in the Affiliate Manager queue.
- The CMO is reviewing a request for a non-standard payout or custom partnership.
- An affiliate's promotional copy needs a claims check before a launch window opens.
- The Retention Analyst's weekly cohort report shows affiliate-driven MRR below 20% of new MRR and the channel needs unblocking.
- An affiliate is suspected of false claims, audience fraud, or payment fraud.

## Inputs

- The applicant's audience evidence (newsletter list size, social handles, prior promotional history).
- US 1099 paperwork or international equivalent on file.
- The current standard payout grid (30% recurring monthly, capped 12 months; 30% one-shot on annual; no payout on lifetime deal window referrals).
- The current approved promotional-claims vocabulary from `library/_marketing/approved-claims.md`.

## Procedure

1. **Screen the applicant.** Audience alignment first — they must speak to solo operators, small agencies, or creators, not generic "make money online" audiences. Check past promotional history for high-pressure tactics, fake scarcity, or income-claim language. Reject quietly if mis-aligned.
2. **Confirm tax / compliance basics.** No live link until paperwork is on file.
3. **Issue the tracking link.** One unique link per affiliate. Default payout: 30% recurring on monthly (12-month cap per referred member), 30% one-shot on annual. Lifetime deal window referrals pay zero — the LTD math already prices the buyer.
4. **Walk them through the claims rules.** Affiliates MAY claim: "Library of 50+ templates, tools, guides, and videos"; "Monthly and annual pricing available"; "Cancel anytime". Affiliates MAY NOT claim: specific results ("make $10K with this template"), that we are a course, that we are a community-only membership, or future asset releases that haven't been announced.
5. **Escalate non-standard payouts.** Any payout above standard requires CMO approval. Any custom partnership (co-branded content, revshare splits, exclusivity) requires Founder approval.
6. **Set the monthly payout cadence.** Payouts run the first business day of each month. Disputes go to the Affiliate Manager first; CMO if unresolved within 7 days.

## Outputs

- `affiliates/<affiliate-slug>/PROFILE.md` — audience evidence, compliance status, tracking link, payout tier, approved-claims acknowledgment, go-live date.
- A monthly payout file at `affiliates/_payouts/<YYYY-MM>.md` reconciled against Billing Specialist data.
- An affiliate-conversion line item handed to the Retention Analyst for the weekly cohort report's "MRR additions by source" breakdown.

## Anti-patterns

- Approving an affiliate with no audience evidence because "the form was filled out".
- Raising the standard payout to win a single affiliate — once the floor moves, every existing affiliate renegotiates.
- Letting an affiliate claim we are a course or a community-only membership — these violate the three identity distinctions in COMPANY.md.
- Paying out on lifetime deal window referrals — the LTD price is already modeled against expected LTV; layering a commission on top makes the window unprofitable.
- Terminating an affiliate for a soft offense without CMO sign-off; only false claims, audience fraud, or payment fraud are unilateral-termination grounds.
- Running affiliate pushes during the first 14 days of a member's onboarding — that traffic isn't ready for the upsell and burns the affiliate's reputation.

## Reference

Pair this skill with:
- `annual-vs-monthly-pricing-strategy` for the price points affiliates promote.
- `lifetime-deal-vs-subscription-modeling` for why LTD windows exclude affiliate payouts.
