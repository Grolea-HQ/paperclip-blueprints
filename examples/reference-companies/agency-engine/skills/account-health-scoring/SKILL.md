---
schema: agentcompanies/v1
slug: account-health-scoring
name: account-health-scoring
description: 'Score every active Agency Engine retainer red / yellow / green every Monday so churn signals surface before MRR moves.'
---

# account-health-scoring

*How Agency Engine scores every active retainer every Monday morning — the ritual that protects $30K MRR from silent churn before revenue moves.*

## When to load this skill

- It is Monday 09:00 and the weekly account health sweep is starting (mandatory cadence; no skips for "busy weeks").
- A QBR brief is being assembled and the Strategist needs the latest 13-week health trend.
- A renewal conversation is inside 30 days and the CEO needs the current color before pricing talks.
- A red account has appeared and the Head of Accounts is escalating to CEO and Director of Operations.
- A new retainer just crossed Day 30 of onboarding and the first formal health score must be recorded.

## Inputs

- The active retainer roster from `PROJECT-INVENTORY.md`.
- Last cycle's Plan → Run → Report artifacts per account.
- Email and call logs since the previous Monday sweep.
- Last weekly score in `clients/<client-slug>/health/<YYYY-WW>.md`.
- The current scope-creep log and any open change orders.

## Procedure

1. **Pull the roster.** Open the active retainer list. Every retainer gets scored — no exceptions, even Day-30 onboardings.
2. **Score each dimension R/Y/G per account.** Use the rubric below. Every score gets a one-line rationale; vibes scores are rejected.
3. **Compute the overall color.** Green = all dimensions green. Yellow = one or two yellow, no red. Red = any red, or three+ yellow.
4. **Weight renewal proximity.** Inside 30 days of renewal, any yellow promotes the overall color one notch toward red.
5. **Trigger actions per color** (see Action triggers below).
6. **File the score.** `clients/<client-slug>/health/<YYYY-WW>.md` with rationale per dimension and trend versus last week.
7. **Roll up to the dashboard.** Update the weekly health summary the CEO and Director of Operations read before Monday standup.

### Scoring rubric

| Dimension | Green | Yellow | Red |
|---|---|---|---|
| Plan → Run → Report cadence honored | All three shipped on schedule | One slipped < 48h | Slip > 48h or missed entirely |
| Client engagement | Approvals < 48h, attended review call | Approvals 48-96h or partial attendance | Approvals > 96h or no-show |
| Scope discipline | Change orders captured, none absorbed | One silent absorption flagged | Repeat silent absorption |
| Performance-vs-plan | Hit success thresholds | Within 20% of threshold | Missed by > 20% |
| Sentiment signal | Warm, forward-looking | Flat or transactional | Cold, frustrated, or escalating |
| Renewal proximity | > 60 days | 30-60 days | < 30 days |

### Action triggers

- **Green:** log the score, move on. No additional action.
- **Yellow:** Account Manager adds a flagged note to the next review call agenda; Strategist reviews in next Plan-week.
- **Red:** 48-hour recovery plan drafted via `churn-prevention-playbook`; CEO and Director of Operations notified same day.
- **Renewal-window yellow or red:** CEO + Strategist + Head of Accounts hold a recovery sync within 72 hours.

## Outputs

- `clients/<client-slug>/health/<YYYY-WW>.md` per account, with R/Y/G scores, rationales, and overall color.
- A weekly health summary entry in the Director of Operations' dashboard.
- A recovery plan kickoff (via `churn-prevention-playbook`) for every red account, same day.
- A QBR-ready 13-week trend block per account every quarter.

## Anti-patterns

- Skipping the Monday sweep "because we're busy" — the ritual is non-negotiable; it is what protects client LTV.
- Scoring on vibes without a one-line rationale per dimension.
- Hiding red signals to avoid a hard CEO conversation — anti-drift requires honest scoring.
- Padding green scores to keep the dashboard pretty for the Founder.
- Treating renewal-proximity weighting as optional when retainers are inside 30 days.
- Letting a red sit beyond 48 hours without a drafted recovery plan.

## Reference

Pair this skill with:
- `churn-prevention-playbook` for the recovery plays once a score turns red.
- `quarterly-business-review-templates` for the QBR brief that rolls up 13 weekly scores.
- `scope-creep-recovery` when scope discipline is the dimension dragging the color down.
