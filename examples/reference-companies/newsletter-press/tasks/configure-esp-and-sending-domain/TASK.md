---
schema: agentcompanies/v1
slug: configure-esp-and-sending-domain
name: 'Configure ESP and sending domain'
project: first-8-issues-cadence-voice
assignee: newsletter-producer
---

# Configure ESP and sending domain

## Objective

Set up Substack, beehiiv, or ConvertKit (per Founder choice) with sending-domain authentication, paid tier wiring, and the segments needed on day one — so the first send goes out cleanly and the paid tier is ready to launch.

## Completion criteria

- SPF, DKIM, and DMARC records configured on the founder's sending domain.
- From-address verified across Gmail, Outlook, and Apple Mail.
- Paid tier configured (monthly + annual) with Stripe (or ESP-native) connected.
- Day-1 segments built: `free-active`, `free-dormant`, `trial`, `paid-active`, `paid-cancelled`.
- Warm-up send plan documented (1,000 / 2,500 / 5,000 / full list across two weeks).
- Setup documented in `distribution/esp-setup.md` and segments in `distribution/segments.md`.