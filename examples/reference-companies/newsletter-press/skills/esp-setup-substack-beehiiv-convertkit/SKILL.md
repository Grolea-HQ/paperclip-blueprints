---
schema: agentcompanies/v1
slug: esp-setup-substack-beehiiv-convertkit
name: esp-setup-substack-beehiiv-convertkit
description: 'Configuring the email service provider — Substack, beehiiv, or ConvertKit — for the founder''s sending domain, paid-tier wiring, and day-one segmentation so the inbox we depend on actually delivers.'
---

# esp-setup-substack-beehiiv-convertkit

*How Newsletter Press wires the email service provider so deliverability, paid tier, and segmentation are working before the first issue ships.*

## When to load this skill

- The founder is launching the newsletter and choosing between Substack, beehiiv, and ConvertKit.
- The Newsletter Producer is configuring a fresh sending domain.
- The Ad Ops Specialist needs the sponsorship-trafficking segments built (free-active vs. paid-active).
- An ESP migration is being debated — the CEO must approve, and this skill is the gating reference.
- Deliverability has degraded (open rate down 4+ points over two weeks) and the sending-domain configuration is the first place we look.

## Inputs

- The founder's chosen sending domain (e.g. `newsletter.foundername.com`) and DNS access.
- Stripe account in the founder's legal entity, ready for connection to the ESP's paid-tier plumbing.
- The first 1,000 free subscribers, if migrating from a prior list — and proof of opt-in for each.
- The voice-guide reference for the from-name and welcome-email tone.

## Procedure

### Phase 1 — Sending domain

1. Set up SPF, DKIM, and DMARC records on the founder's sending domain. DMARC starts in `p=none` for two weeks, then moves to `p=quarantine`.
2. Verify the from-address renders as `Founder Name <hello@domain.com>` in Gmail, Outlook, and Apple Mail. Not "via substack.com." Not a no-reply address.
3. Warm-up sends in the first two weeks: 1,000 / 2,500 / 5,000 / full list. Do not blast cold from day 1 — deliverability collapses for months.

### Phase 2 — Paid tier wiring

Pick the ESP, then wire the paid plumbing exactly as below.

| ESP | Paid plumbing |
|---|---|
| Substack | Native paid tier; configure monthly ($8) + annual ($80); Stripe connected; tax handled by Substack; founder owns the URL |
| beehiiv | Premium tier; Stripe Connect; configure free vs. paid feeds; custom domain mapped |
| ConvertKit | Commerce; configure subscription product; segment based on purchase tag; landing page hosted on ConvertKit until custom domain ready |

### Phase 3 — Day-one segments

Build these five segments before the first send. Every later workflow — sponsorship trafficking, cohort churn, welcome sequence, win-back — assumes they exist.

- `free-active` — opened in last 30 days.
- `free-dormant` — no open in 60 days; eligible for re-engagement send only, never surveys, never sponsorship reach.
- `trial` — paid trial in progress.
- `paid-active` — paying.
- `paid-cancelled` — cancelled, retained 60 days for win-back, then deleted.

### Phase 4 — Verification send

Ship a deliverability-test issue to the founder, the Managing Editor, and three external inboxes (one Gmail, one Outlook, one Apple Mail). Read it on a phone. If the from-name, paid-tier CTA, or unsubscribe link looks off in any inbox, fix before public launch.

## Outputs

- `operations/esp/config.md` — chosen ESP, sending domain, DKIM/SPF/DMARC status, paid-tier price points, segment definitions.
- `operations/esp/warmup-log.md` — the two-week ramp, with open rate per ramp send.
- A one-page CEO-readable launch-readiness note: deliverability green, paid wiring green, segments live.

## Anti-patterns

- Importing a cold list. Newsletter Press only sends to subscribers who opted in directly to this publication. A cold import kills the sending domain for everyone downstream.
- Switching ESPs without CEO approval and a 30-day migration plan. Cadence and deliverability suffer for weeks; the operating heartbeat slips.
- Skipping the warm-up because the founder "already has a domain reputation." Reputation does not transfer to a new sending subdomain.
- Configuring paid-tier pricing without CEO sign-off. Pricing changes always escalate; defaults ($8/$80) are not law, but changes go through the CEO.
- Mapping `free-dormant` into surveys, sponsorship reach, or cross-promo swaps. They are out of the audience until re-engaged.
- Leaving DMARC at `p=none` past week two. That is a deliverability commitment we make once.

## Reference

Pair this skill with:
- `welcome-sequence-authoring` — the first thing the configured ESP needs to send.
- `sponsorship-rate-card` — pricing is graded against segments built here.
