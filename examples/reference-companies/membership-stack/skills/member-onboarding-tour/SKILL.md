---
schema: agentcompanies/v1
slug: member-onboarding-tour
name: member-onboarding-tour
description: 'The first-week journey every new Membership Stack member walks through — landing them on a first useful asset under five minutes, suppressing upsells, and locking down the metrics that predict month-two retention.'
---

# member-onboarding-tour

*The first five minutes decide whether they stay past month one. We treat onboarding as a retention surface, not a marketing surface.*

## When to load this skill

- A new member signs up and the welcome screen renders.
- The Platform Engineer is wiring or revising the onboarding flow trigger.
- The Member Success Lead is revising the day-3 or day-7 email copy.
- The Retention Analyst flags that first-asset-open rate has slipped below 75% and onboarding needs review.
- The quarterly cohort survey returns a pattern indicating onboarding confusion.

## Inputs

- The member's signup plan (monthly or annual), source (organic, affiliate, paid).
- The current top-three "goal" options from the latest quarterly survey readout.
- The currently-recommended starter asset for each goal — refreshed by the Product Manager and Member Success Lead together.
- The community welcome prompt of the week (Community Manager).

## Procedure

1. **Welcome screen.** One sentence: "You're in. Here's how the library is organized." No marketing copy, no upgrade prompt, no profile gate.
2. **Pick your goal.** Three options drawn from the top-three reasons members cite in the latest quarterly survey. Three is the cap — overwhelm is the #1 onboarding failure mode.
3. **First asset surfaced.** Based on the goal pick, link straight into one specific asset — not a category page, not a library home, not a list. One asset, opened.
4. **Community ping.** Community Manager DMs a welcome with a single concrete prompt ("Reply with the one thing you're trying to ship this week"). Replies thread into the community space, not into a one-on-one channel.
5. **Day 3 email.** Member Success Lead sends a "have you opened your first asset?" check. Named human, monitored inbox. If the answer is no, the email asks why — not pushes a different asset.
6. **Day 7 survey.** Single-question survey: "Did your first week deliver?" — three options. Routes into `analytics/survey-log.md` per the member-survey-protocol.

## Success measures

- 75%+ of new members open at least one asset within their first session.
- 50%+ reply to the community welcome DM within seven days.
- Day 7 survey response rate above 30%.

## Owners

- Tour copy: Member Success Lead.
- Tour wiring: Platform Engineer.
- Community DM and follow-up: Community Manager.
- Day 3 and Day 7 emails: Member Success Lead, reviewed by Content Director.
- Metric readout: Retention Analyst, in the weekly cohort report.

## Outputs

- `library/_onboarding/tour-v<n>.md` — current tour copy, decision tree, and the asset-mapping table from goal-pick to first-asset link.
- A first-asset-open metric and Day 7 survey response line in the weekly cohort report.
- A first-week cancel-reason summary (when sequence C fires inside the first 7 days) for the Retention Analyst.

## Anti-patterns

- Pitching an annual upgrade during onboarding — the annual upsell waits until day 30. Pushing earlier trains members to associate signup with sales pressure and depresses month-two retention.
- Forcing a profile-completion gate before the first asset — every gate is a drop-off point. Profile data, if needed at all, comes after the first asset open.
- Showing every category on the welcome screen — overwhelm is the documented #1 failure mode; three goal options is the cap.
- Sending the day-3 email from a no-reply address — every onboarding touch is from a named human (Member Success Lead) at a monitored inbox.
- Linking the goal-pick to a category page instead of a specific asset — "browse the templates folder" is not a first-asset experience; one named asset is.
- Treating the day-7 survey as a long survey — one question, three options. The member-survey-protocol governs anything longer.

## Reference

Pair this skill with:
- `member-survey-protocol` for the day-7 single-question survey and quarterly readout.
- `asset-library-architecture` for the asset path the goal-pick links into.
