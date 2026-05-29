---
schema: agentcompanies/v1
slug: churn-prevention-playbook
name: churn-prevention-playbook
description: 'Recovery plays for every common SMB-retainer churn failure mode so red-status accounts are saved (or honestly walked away from) inside 30 days.'
---

# churn-prevention-playbook

*How Agency Engine recovers a red account inside 30 days — or walks away honestly. The library of plays that defends 85%+ gross retention.*

## When to load this skill

- An account has scored red on the Monday `account-health-scoring` sweep.
- An account inside 30 days of renewal has scored yellow on any dimension.
- The CEO has flagged a client risk from a sponsor-side conversation that did not show up in metrics yet.
- A retainer cycle has slipped past Day 5 with no recovery plan in motion.
- A QBR brief surfaced a churn signal that the weekly sweep had not yet caught.

## Inputs

- Latest `clients/<client-slug>/health/<YYYY-WW>.md` score with rationale per dimension.
- The signed SOW from `scope-of-work-builder` so any re-scope conversation has a baseline.
- Last cycle's Client Reporting Pack to confirm whether performance-vs-plan was a factor.
- The scope-creep log for the account (silent absorption is one of the most common drivers).
- The CEO and Director of Operations on standby for same-day escalation.

## Procedure

1. **Diagnose the failure mode.** Map the red signals to one (or more) of the six common modes below. Multiple modes can stack; address the dominant one first.
2. **Draft the recovery plan within 48 hours.** Head of Accounts owns the draft; the plan names the responsible agent, the client-side action requested, and a 30-day re-score date.
3. **CEO review.** No recovery plan goes to the client without CEO sign-off when re-scope or pricing is in play.
4. **Run the client conversation.** Account Manager schedules within 5 business days of the red. Honest framing, no over-promising.
5. **Execute the play.** The named agent leads execution; Head of Accounts tracks daily.
6. **Re-score at Day 14 and Day 30.** Either the account returns to yellow/green, or we draft the honest walk-away conversation.

### Common failure modes and plays

1. **Cadence slip.** Director of Operations and Project Manager re-anchor the Plan → Run → Report cycle; CEO emails the client acknowledging the slip with a concrete recovery cadence.
2. **Results below plan.** Strategist re-runs Plan-week strategy with sharper objectives; Analyst surfaces attribution truth; Account Manager hosts an honest review call (no spin).
3. **Scope-creep absorption.** Re-scope conversation hosted by Head of Accounts + CEO — explicit re-tiering up or scope reduction; the absorption stops on the call.
4. **Communication gap.** Account Manager moves to weekly check-ins; CEO joins next monthly review call to re-anchor sponsor confidence.
5. **Voice or craft drift.** Creative Director re-runs `brand-voice-capture`; QA bar visibly tightened on the next deliverable batch.
6. **Sponsor turnover on the client side.** Re-introduction kit drafted by Account Manager; CEO joins next call; cadence rebuilt from Day 1.

### Recovery timeline

- **Day 0:** Red flagged on Monday sweep.
- **Day 1-2:** Recovery plan drafted by Head of Accounts.
- **Day 3-5:** Recovery plan reviewed with CEO; client conversation scheduled.
- **Day 7:** Client check-in call held.
- **Day 14:** Recovery progress review with Director of Operations.
- **Day 30:** Status reassessed — green, yellow, or honest walk-away conversation initiated.

## Outputs

- `clients/<client-slug>/recovery/<YYYY-MM-DD>.md` — the recovery plan with failure mode, responsible agents, client-side asks, and re-score dates.
- A re-scored entry in `clients/<client-slug>/health/<YYYY-WW>.md` at Day 14 and Day 30.
- Either a renewed SOW, a re-tiered SOW, or a documented honest walk-away letter.

## Anti-patterns

- Sitting on a red account past 48 hours — the cost compounds daily.
- Recovery via promises rather than re-scope — sentiment temporarily lifts but the failure mode recurs.
- Saving an account by giving away work outside the SOW — kills the retainer math and trains the client that scope is negotiable.
- Letting the conversation stay between Account Manager and the client when CEO presence is what re-anchors trust.
- Skipping the Day 30 honest reassessment because "things feel better" — vibes are not a metric.
- Walking away from an account without a written exit letter; future renewal stories suffer.

## Reference

Pair this skill with:
- `account-health-scoring` — the upstream signal that triggers this play.
- `scope-creep-recovery` for the most common churn driver.
- `quarterly-business-review-templates` when recovery overlaps a QBR window.
