---
schema: agentcompanies/v1
slug: pricing-and-proposal-templates
name: pricing-and-proposal-templates
description: 'Defensible Foundation / Growth / Scale tier pricing and proposal templates used in every pitch, renewal, and re-tier conversation.'
---

# pricing-and-proposal-templates

*How Agency Engine prices retainers and writes proposals — the three-tier template that holds in every pitch and every renewal, with defensibility memos behind every number.*

## When to load this skill

- The CEO is drafting a new retainer pitch and needs the current tier definitions and pricing bands.
- The Finance Controller is authoring the quarterly defensibility memo for one or more tiers.
- The Account Manager is preparing a renewal or re-tier conversation and needs tier rationale.
- A QBR has surfaced a re-tier recommendation (up or down) and the Head of Accounts needs the pricing logic.
- A prospect is negotiating a non-standard price and the CEO is deciding whether to escalate to Founder sign-off.

## Inputs

- The current tier definitions table (see Tier definitions below).
- The latest Finance Controller defensibility memo per tier (refreshed quarterly).
- The agency's per-retainer gross margin target (set by Founder, reviewed quarterly).
- Observed renewal rates per tier from the last 12 months.
- The signed SOW template from `scope-of-work-builder`.

## Procedure

1. **Match the prospect or account to a tier.** Use the tier definitions table; budget is necessary but not sufficient — channel scope and cadence are equally weighted.
2. **Pull the defensibility memo for that tier.** The memo is the rationale that survives a "why this price" question on a sales or renewal call.
3. **Draft the proposal** using the proposal template structure (below). Every proposal cites: tier, scope-in, scope-out, cadence, reporting cadence, term, and change-order policy.
4. **Sanity-check with Finance Controller** when the deal lands inside the tier band's bottom 20% or proposes any non-standard inclusion.
5. **Founder sign-off** for any pricing outside the published bands or any equity / commission alternative (always declined per company constraints).
6. **Send under CEO signature** — no proposal goes out unsigned.

### Tier definitions

| Tier | Monthly band | Channel scope | Cadence | Reporting | Roster |
|---|---|---|---|---|---|
| Foundation | $2.5K - $4K | One channel focus | Monthly Plan → Run → Report | Monthly client report | Account Manager + 1 channel lead |
| Growth | $4K - $8K | Multi-channel (paid + SEO + lifecycle) | Bi-weekly cadence | Monthly + quarterly QBR | Account Manager + Strategist + 2-3 channel leads |
| Scale | $8K - $15K | Full-service all channels | Weekly cadence | Monthly + monthly QBR | Dedicated Strategist + Account Manager + all channel leads |

### Defensibility memo (Finance Controller authors quarterly per tier)

- **Roster hours per cycle** the tier consumes (concrete number, not "varies").
- **Channel surface** the tier covers (which channels at what depth).
- **Reporting cadence** the tier sustains (monthly / bi-weekly / weekly).
- **Per-retainer gross margin target** for the tier.
- **Observed renewal rate** for the tier over trailing 12 months.

### Proposal template (every proposal cites these eight blocks)

- **Plan → Run → Report cadence** as the lead.
- **Tier and pricing** with monthly amount and term.
- **Scope-in.** Channels and deliverable cadence per channel.
- **Scope-out.** Channels explicitly excluded.
- **Reporting cadence.** Day-3 monthly report, QBR schedule.
- **Escalation model.** Account Manager primary, CEO approves, Founder approves tier changes.
- **Change-order policy.** Per `scope-creep-recovery`.
- **Onboarding.** 14-day sequence per `client-onboarding-sequence`.

## Outputs

- A proposal document filed at `clients/<client-slug>/proposals/<YYYY-MM-DD>.md` with all eight template blocks complete.
- A defensibility memo at `finance/defensibility/<tier>-<YYYY-Q>.md`, refreshed quarterly.
- A re-tier recommendation memo (when applicable) filed at `clients/<client-slug>/strategy/retier-<YYYY-MM-DD>.md`.
- A Founder sign-off log entry for any non-standard pricing.

## Anti-patterns

- Non-standard pricing without Founder sign-off — every deviation is logged, no exceptions.
- Tier pricing changes outside QBR season without a refreshed Finance Controller defensibility memo.
- Proposals that don't cite the SOW change-order policy — the buyer then assumes scope is negotiable verbally.
- Equity-for-services or commission-only deals — declined per `COMPANY.md` constraints.
- Discounting Foundation tier below $2.5K to "win the logo" — kills retainer math; declines instead.
- Proposals that lead with channel deliverables instead of the Plan → Run → Report cadence — sells the wrong thing.

## Reference

Pair this skill with:
- `retainer-pitch-authoring` for pitch narrative.
- `scope-of-work-builder` for converting proposal to signed SOW.
- `quarterly-business-review-templates` for re-tier conversations at renewal.
