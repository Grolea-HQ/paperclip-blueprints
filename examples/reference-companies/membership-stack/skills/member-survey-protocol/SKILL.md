---
schema: agentcompanies/v1
slug: member-survey-protocol
name: member-survey-protocol
description: 'How Membership Stack runs exactly one quarterly cohort survey and three event-triggered single-question surveys — protecting member attention while still feeding the Retention Analyst the signal needed to call positioning shifts and asset gaps.'
---

# member-survey-protocol

*Surveys are a tax on member attention. We pay it sparingly — one quarterly survey, three trigger surveys, nothing else.*

## When to load this skill

- A calendar quarter is closing (weeks 12, 24, 36, 48) and the cohort survey needs to fire.
- A member hits day 7 of membership and the onboarding-quality trigger survey fires.
- A member confirms a cancel and the cancel-reason survey fires.
- A member converts from monthly to annual and the trigger survey fires.
- The Retention Analyst is reviewing survey responses for the 5-in-30-days action threshold.

## Inputs

- The member's tenure, plan, and most recent activity (asset opens, community posts).
- The 14-day no-double-survey lockout on the member's record.
- The current top-three "wish-we-had" themes from the most recent quarterly readout.
- Cancel volume and annual conversions for the period (drive the trigger-survey populations).

## The two survey families

### 1. Quarterly cohort survey

- **5 questions max.** No more, ever.
- **One open-text question:** "What's the one asset you wish we had?"
- **Schedule:** weeks 12, 24, 36, 48 of the year.
- **Owner:** Member Success Lead administers; CEO and Retention Analyst read out.

### 2. Trigger surveys (three, single-question each)

| Trigger | Question | Owner |
|---|---|---|
| Day 7 of membership | "Did your first week deliver?" (3 options) | Member Success Lead |
| Cancel confirmation | "Why?" (1 open-text) | Member Success Lead |
| Annual upgrade | "What pushed you over?" (3 options + open-text) | CMO |

## Procedure

1. **Check the lockout.** No survey within 14 days of any other survey sent to the same member. The lockout protects against fatigue and is non-negotiable.
2. **Fire the survey.** Quarterly cohort runs on its calendar; trigger surveys fire on the named event.
3. **Log every response.** All responses land in `analytics/survey-log.md` with member ID, plan, tenure, response, and timestamp.
4. **Pattern-detect.** A pattern triggers action when 5+ members in a 30-day window flag the same concern. Anything below that threshold is noise — do not surface it.
5. **Route the pattern.** The Retention Analyst surfaces the pattern in the weekly cohort report. The CEO decides whether it becomes a positioning shift (Founder approval needed) or a calendar slot (CEO-approvable).
6. **Close the loop.** Quarterly cohort survey gets a public-to-members readout summarizing the top three themes and what we're doing about them. Closes within 14 days of the survey closing.

## Outputs

- `analytics/survey-log.md` — every response, timestamped and tagged.
- A quarterly readout summary handed to the CEO and Founder.
- A "wish-we-had" theme list handed to the Product Manager for asset library growth prioritization.
- A cancel-reason cohort line in the Retention Analyst's weekly cohort report.
- A public-to-members quarterly summary post (Community Manager publishes).

## Anti-patterns

- Asking members to rate features 1–10 — they don't, and the data is noise.
- Running NPS in addition to the above — pick one signal; we run trigger surveys, not NPS theatre.
- Paying for survey responses — incentives skew the answers and the Retention Analyst can no longer trust the pattern.
- Sending a second survey within 14 days of the first to the same member — the lockout exists exactly to prevent this and overrides every campaign calendar.
- Acting on a single complaint as if it were a pattern — under the 5-in-30-days threshold, it is noise. The threshold is the gate.
- Letting the quarterly readout stay private — members surveyed deserve to see the rollup within 14 days, or response rates collapse next quarter.

## Reference

Pair this skill with:
- `churn-save-email-flow` for the cancel-confirmation trigger survey.
- `member-onboarding-tour` for the day-7 trigger survey.
