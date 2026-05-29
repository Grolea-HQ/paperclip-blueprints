---
schema: agentcompanies/v1
slug: retainer-pitch-authoring
name: retainer-pitch-authoring
description: 'Author SMB-grade retainer pitches that lead with the Plan to Run to Report cadence rather than volume claims or growth-hack promises.'
---

# retainer-pitch-authoring

*How Agency Engine writes a pitch — the one that wins SMB buyers on rhythm and discipline, not on per-post pricing or growth-hack promises.*

## When to load this skill

- The CEO is opening a new outbound or inbound retainer conversation and a pitch document is required.
- The Copywriter is drafting outbound pitch copy for the agency's own outreach.
- The Finance Controller is sanity-checking a proposed pitch's profitability against tier defensibility.
- A re-pitch is being prepared after a prospect went cold and the original framing needs refresh.
- A tier-upgrade pitch is being drafted for an existing client moving Foundation → Growth or Growth → Scale.

## Inputs

- The discovery notes from the CEO call via `discovery-call-playbook`.
- The current tier definitions and defensibility memos from `pricing-and-proposal-templates`.
- The brand voice document (the agency's own) for pitch tone consistency.
- The Strategist's draft of the discovery brief for prospects advancing to SOW.
- The Finance Controller's gross margin target per tier.

## Procedure

1. **Confirm tier.** Match the prospect to Foundation / Growth / Scale using `pricing-and-proposal-templates`. If outside any tier, escalate to Founder before drafting.
2. **Open with cadence.** The first slide / first section is Plan → Run → Report — the buyer is buying a rhythm, not a launch.
3. **Define scope concretely.** Channels in, channels out. Deliverable cadence per channel. No "as needed" volume.
4. **Show the reporting cadence.** Day-1-2 month-end close, Day-3 client report, QBR every quarter.
5. **Name the escalation model.** Account Manager primary contact, CEO approves external changes, Founder approves tier changes.
6. **State pricing and term.** Monthly retainer billed in advance, 90-day initial term, month-to-month thereafter.
7. **Walk the 14-day onboarding.** From `client-onboarding-sequence`. The buyer sees the work begin.
8. **Close with the renewal narrative.** What QBR looks like, how renewal decisions get made, why we're built to renew not to launch-and-leave.

### Pitch structure (eight blocks, in order)

1. **The Plan → Run → Report cadence.** Lead, not bury.
2. **The retainer tier.** Foundation / Growth / Scale with concrete deliverable cadence.
3. **The scope of work.** In-scope channels, out-of-scope channels, cadence per channel.
4. **The reporting cadence.** Weekly internal, monthly client report by Day 3, quarterly QBR.
5. **The escalation model.** Named contacts and approval gates.
6. **Pricing and term.** Monthly retainer in advance, 90-day initial term.
7. **Onboarding.** 14-day sequence with named deliverables.
8. **Renewal narrative.** QBR, re-tier mechanics, why we're built to renew.

## Outputs

- A pitch document or deck filed at `clients/<client-slug>/pitches/<YYYY-MM-DD>.md` with all eight blocks.
- CEO sign-off and Finance Controller profitability check filed before send.
- A draft SOW skeleton ready for `scope-of-work-builder` if the pitch is verbally accepted.
- A re-pitch memo for prospects who went cold, citing what changed in the framing.

## Anti-patterns

- Project-only framings ("we'll launch X for you") — kills retainer math; if the prospect only wants a project, decline or convert to retainer within 60 days.
- Per-asset pricing ("$200 per post") — destroys the cadence sale; explicitly off the table.
- Volume promises ("30 posts a month, 4 ads a week") — volume is a side effect of strategy, never the deliverable; pitches that lead with volume attract churn-prone buyers.
- Growth-hack language ("we'll find the unlock that 10x's your growth") — we are not a growth shop; this attracts the wrong fit and disappoints.
- Non-standard pricing without Founder sign-off — every deviation logged, no exceptions.
- Pitches that bury the renewal narrative — the buyer can't visualize the long arc, the deal closes shorter and renews worse.

## Reference

Pair this skill with:
- `discovery-call-playbook` for the discovery that precedes the pitch.
- `pricing-and-proposal-templates` for tier definitions and defensibility.
- `scope-of-work-builder` for the SOW that follows verbal acceptance.
