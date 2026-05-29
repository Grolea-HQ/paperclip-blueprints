---
schema: agentcompanies/v1
slug: audience-survey-protocol
name: audience-survey-protocol
description: 'Running onboarding, quarterly NPS, and annual deep surveys against subscribers so we learn what readers actually pay for — without polluting the open-rate signal or burning the list.'
---

# audience-survey-protocol

*How Newsletter Press asks subscribers questions without breaking the inbox we depend on.*

## When to load this skill

- The Growth Lead, Open/Click Analyst, Research Analyst, or Churn Analyst is about to send a survey to any segment.
- A new welcome sequence is being authored and email #5 needs the onboarding survey block.
- It is the first Monday of a new quarter and the paid-tier NPS is due.
- The annual deep survey window is open (one month every twelve).
- A pricing or paid-tier offer change is being debated and the CEO has asked for reader-stated preference data before approval.

## Inputs

- Subscriber segments from the ESP (Substack, beehiiv, or ConvertKit): `free-active`, `paid-active`, `paid-cancelled`. Never `free-dormant` — they cannot consent to a survey they will not open.
- The latest cohort retention table from `cohort-churn-tracking` (so survey results can be cross-read against actual churn behavior, not just stated intent).
- The voice guide at `editorial/voice-guide.md` — every survey question must read in the founder's voice.
- A live tally of surveys sent in the trailing 90 days. If the segment already received one, stop.

## Procedure

1. **Pick the right survey for the moment.** Three exist, no others.
   - **Onboarding survey** — three questions inside welcome email #5 only. Optional. One free-text field: *"What made you subscribe?"*
   - **Quarterly NPS** — paid subscribers only. One question + one open-text follow-up: *"How likely are you to recommend [newsletter] to one peer? (0–10)"* then *"What would make it a 10?"*
   - **Annual deep survey** — all active subscribers, anonymous, 8–10 questions, capped at 4 minutes.
2. **Write questions in the founder's voice.** No "On a scale of strongly disagree to strongly agree." Replace leading framing ("How much do you love…") with neutral framing ("What about X is most useful?").
3. **Hold the cadence wall.** No segment receives more than one survey per quarter. Survey fatigue lowers reply rates on every future survey for six months — this rule is not negotiable.
4. **Run the send through the Newsletter Producer.** Surveys ship through the same ESP as issues, with the same sending domain, on a non-issue day.
5. **Wait seven days, then close.** Late replies skew toward power-readers and overstate satisfaction.
6. **Publish the report.** Always include sample size, response rate, segment definition, and one stated caveat. A 100-reply survey against a 10,000-list is directional, not representative.

## Outputs

- `analytics/surveys/<YYYY-MM>-<survey-type>.md` — questions, response count, response rate, top three themes from open text, recommended actions, sample-size caveat.
- A one-page summary appended to the Analytics weekly roll-up if the survey returned a finding the CEO should act on.
- An updated banned-questions list in `analytics/surveys/leading-questions.md` whenever a question backfires.

## Anti-patterns

- Running a survey to fill an idle afternoon. Surveys cost reply-rate equity; spend it on a question the CEO will actually answer.
- Surveying `free-dormant` subscribers to "win them back." They unsubscribed in spirit already.
- Treating a 1.2% reply rate as a mandate. Caveat the sample or do not publish.
- Asking leading questions that pre-confirm a pricing change the CEO already wants to make.
- A/B testing question wording across the same survey. The result is unreadable.
- Surveying the paid tier more than once a quarter. Paid subscribers churn faster when we ask them to grade us repeatedly.

## Reference

Pair this skill with:
- `cohort-churn-tracking` to cross-check stated intent against observed retention.
- `paid-tier-conversion-funnel` when NPS replies suggest a welcome-sequence rewrite.
