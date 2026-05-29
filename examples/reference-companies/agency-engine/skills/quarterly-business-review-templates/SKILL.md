---
schema: agentcompanies/v1
slug: quarterly-business-review-templates
name: quarterly-business-review-templates
description: 'Run the 90-day QBR as a structured renewal conversation with a results narrative, an honest miss section, and an explicit next-quarter plan.'
---

# quarterly-business-review-templates

*How Agency Engine runs the QBR — the 90-day renewal conversation that decides re-tier, re-scope, or honest walk-away, every retainer, every quarter.*

## When to load this skill

- A retainer is inside 14 days of its quarter-end and the QBR brief needs to be assembled.
- A renewal decision date is approaching (90-day initial term or quarterly renewal point).
- A red account from `account-health-scoring` is being given a QBR-style structured reset conversation outside the normal cadence.
- A tier-change recommendation is being prepared and needs the QBR brief as supporting evidence.
- A new Scale-tier retainer is finishing its first quarter and the monthly-QBR cadence begins.

## Inputs

- The trailing three `client-reporting-pack` monthly reports for the quarter.
- The trailing 13 `account-health-scoring` weekly scores.
- The signed SOW and any change orders executed during the quarter.
- The quarter's monthly plans from `monthly-strategy-review` — defines what objectives we were measuring against.
- Captured client signals (sponsor feedback, sentiment shifts) from the Account Manager's log.

## Procedure

The QBR has two phases: a brief assembled in the week before the call, and the 60-minute call itself.

### Brief assembly (week before the call)

1. **Results-vs-objectives.** The quarter's plan vs. the quarter's outcomes, one row per objective.
2. **Wins.** Concrete, evidence-cited, attributable to the work — no vanity claims.
3. **Misses.** Honest. Each with a one-line "why" and a remediation owner.
4. **Account health summary.** The 13 weekly scores plus trend; latest color called out.
5. **Client signals.** Captured asks, scope-creep history, change orders executed.
6. **Renewal recommendation.** One of: renew at current tier / re-tier up / re-tier down / decline to renew.
7. **Next quarter's objectives.** Drafted by Strategist, reviewed by CEO before the call.

### Call structure (60 minutes)

1. **(10 min) Recap the quarter.** Account Manager and Strategist walk results.
2. **(20 min) What worked and what didn't.** Honest, sourced — the misses get equal airtime to the wins.
3. **(15 min) Next quarter.** Strategist proposes objectives; client weighs in on priorities.
4. **(10 min) Scope, tier, pricing.** Head of Accounts leads the renewal conversation; CEO available if escalation needed.
5. **(5 min) Confirm next step.** Renewal decision recorded same day; SOW or change order drafted within 5 business days.

### Roles on the call

- **Head of Accounts:** owns the call, leads renewal conversation.
- **Strategist:** presents next-quarter objectives; must be present (QBRs without Strategist are rejected).
- **Account Manager:** walks results, captures decisions live.
- **Reporting Engineer:** on standby for any data question that escalates.
- **CEO:** joins for tier-change or escalation; otherwise on standby.

## Outputs

- A QBR brief filed at `clients/<client-slug>/qbr/<YYYY-Q>-brief.md` with all seven sections.
- A renewal decision recorded same day at `clients/<client-slug>/qbr/<YYYY-Q>-decision.md`.
- A refreshed SOW or change order within 5 business days when re-tier or re-scope is the decision.
- A next-quarter objectives document fed into the first `monthly-strategy-review` of the new quarter.
- A QBR-aligned brand voice refresh kicked off via `brand-voice-capture` if voice drift surfaced.

## Anti-patterns

- QBRs that skip the misses section — every miss is named with a "why" and a remediation owner.
- QBRs without a renewal recommendation in the brief — the call drifts without a starting position.
- QBRs run by Account Manager alone — Strategist must be present; otherwise the next-quarter objectives lack strategic grounding.
- Treating QBR as a sales call — it is a renewal-and-reset conversation; over-pitching at QBR signals weakness.
- Burying the renewal recommendation as a footnote — the recommendation leads the brief, not the prose summary.
- Deferring the renewal decision past the call — the loop must close same day; ambiguity becomes churn.

## Reference

Pair this skill with:
- `client-reporting-pack` — three monthly reports roll up into the QBR brief.
- `account-health-scoring` — 13 weekly scores supply the trend.
- `pricing-and-proposal-templates` for re-tier conversations.
- `churn-prevention-playbook` when the QBR reveals a recovery path.
