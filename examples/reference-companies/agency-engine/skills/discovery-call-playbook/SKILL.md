---
schema: agentcompanies/v1
slug: discovery-call-playbook
name: discovery-call-playbook
description: 'Run the 45-minute CEO-led discovery call that qualifies SMB retainer fit and ends with a defined next step (SOW or decline).'
---

# discovery-call-playbook

*How the CEO runs an Agency Engine discovery call — 45 minutes, defined output, no fishing expeditions; advances to SOW or declines with reason.*

## When to load this skill

- The CEO has a discovery call booked with an inbound or outbound SMB prospect.
- The Strategist is about to draft a discovery brief from CEO call notes and needs to verify completeness.
- A re-discovery is being run because a prospect went cold for > 30 days and the CEO wants to re-qualify.
- A referral lead is being qualified and needs the same structured pass as cold inbound.
- A prospect from a prior decline is re-approaching and the original disqualifier needs re-testing.

## Inputs

- The lead record (source, fit notes, prior touches, budget hints).
- The latest pricing-and-proposal tiers (Foundation / Growth / Scale) ready in head.
- The agency's positioning constraints — what we will not do, which verticals are off-limits.
- A 45-minute calendar block (no longer; if it overruns, the prospect is not buying cadence).
- The discovery notes template at `agents/ceo/memory/discoveries/<client-slug>-<YYYY-MM-DD>.md`.

## Procedure

The call is 45 minutes, time-boxed. The CEO drives. Notes are taken live.

1. **(5 min) Frame.** Cadence overview — Plan → Run → Report, monthly retainer, no project math. Set the buyer's expectation that they're buying a rhythm, not a launch.
2. **(10 min) Business diagnosis.** Their model, customers, current channels, what's working, what's stuck. Two specific failure-mode questions: "What's the last thing an agency did for you that you wish you'd never paid for?" and "What's the deliverable cadence you actually need?"
3. **(10 min) Goals and constraints.** 12-month outcome, budget reality (asked directly, not danced around), channel preferences, channels off-limits, internal stakeholders.
4. **(10 min) Current stack and history.** Existing tools (CRM, email, analytics), prior agency experience, in-house roles, who owns what internally.
5. **(5 min) Tier sketch.** CEO sketches which tier (Foundation / Growth / Scale) fits and why, out loud, in front of the prospect.
6. **(5 min) Next step.** Either: SOW within 5 business days, or: explicit decline with reason. No "let me think about it" exits — the CEO closes the loop.

### Qualification thresholds

- Budget below Foundation tier ($2.5K/mo): polite decline; refer if possible.
- Industry incompatible with positioning constraints: decline with reason.
- Channel preferences entirely outside service lines: decline; refer if a relationship exists.
- "Project only" buyer below $5K: decline; we don't do project math.
- Reasonable fit on budget, scope, and timeline: advance to SOW within 5 business days.
- Founder-buyer with a coachable read on cadence (not chasing growth-hacks): advance, even at Foundation tier.

## Outputs

- CEO notes filed at `agents/ceo/memory/discoveries/<client-slug>-<YYYY-MM-DD>.md` with all six blocks completed.
- A typed decision (advance / decline / re-engage-later) in the lead record within 24 hours of the call.
- If advancing: a brief to the Strategist to draft the discovery brief within 5 days.
- If declining: a one-paragraph decline letter (warm, honest, with referral if possible).
- A tier sketch in the notes that the Account Manager will use as the SOW starting point.

## Anti-patterns

- Letting the call run past 45 minutes — a prospect who can't accept time discipline will not respect cadence.
- Skipping the budget question because it feels awkward — every disqualifier surfaces later more expensively.
- Pitching mid-discovery — discovery is for capture, not pitch; the pitch is what `retainer-pitch-authoring` is for.
- Closing with "let me get back to you" instead of "SOW within 5 business days or decline" — ambiguity kills the loop.
- Advancing a prospect chasing growth-hacks or per-post pricing because the dollar amount is large — they will churn at month 4.
- Writing decline letters that are vague — every decline names the specific disqualifier; referrals when honest.

## Reference

Pair this skill with:
- `retainer-pitch-authoring` for the post-discovery deck.
- `scope-of-work-builder` for the SOW that follows an advance decision.
- `pricing-and-proposal-templates` for the tier sketch reference.
