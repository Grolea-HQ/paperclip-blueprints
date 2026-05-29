---
schema: agentcompanies/v1
slug: subject-line-ab-testing
name: subject-line-ab-testing
description: 'Running three-candidate subject-line splits on every free-list send so open-rate learning compounds in the log — never on the paid tier, never on topic, only on frame.'
---

# subject-line-ab-testing

*How Newsletter Press splits subject lines on every free send so open-rate learning compounds, without ever testing on the paid tier where consistency is the product.*

## When to load this skill

- The Newsletter Producer is about to schedule a free-list send.
- The Managing Editor needs three candidate framings for the issue going out this week.
- It is the first Monday of a new month and the rolling subject-line log needs its monthly roll-up.
- The Open/Click Analyst notices the rolling 30-day open rate has drifted and the winners-by-frame pattern needs re-reading.
- The Paid Tier Manager asks whether a welcome-sequence subject can be tested — the answer comes from this skill.

## Inputs

- The drafted issue, with the founder's working title.
- The voice guide at `editorial/voice-guide.md` — every candidate must read on-voice.
- The current subject-line log at `analytics/subject-line-log.md` — winners by frame across the rolling 12 sends.
- The list size at send time, to pick the split percentages.

## Procedure

1. **Draft three candidates.** Never four. Three is the working memory bar for the Managing Editor and the only number that lets us read patterns across the log.
   - **Candidate 1 — curiosity.** A question or a withheld noun.
   - **Candidate 2 — benefit.** What the reader walks away with, plainly stated.
   - **Candidate 3 — contrarian.** A claim that opposes the consensus take in the niche.
2. **Pass each through the voice guide.** Strip banned phrases. If a candidate cannot survive the voice guide, replace it — do not ship a winner that drifts the moat.
3. **Pick the split by list size.**

| List size | Split |
|---|---|
| Below 2,500 subs | 50/50 between two candidates; the third is held |
| 2,500 – 10,000 | 30/30/40 with the winner sent to the 40% holdout |
| Above 10,000 | 20/20/60 with the winner sent to the 60% holdout |

4. **Wait the right window.** Send variants two hours before the holdout. Pick the winner on **two-hour open rate**, not 30-minute — early opens skew toward power-readers and overstate the lift.
5. **Send the winner to the holdout.** Same body, winning subject.
6. **Log every result to `analytics/subject-line-log.md`.** Date, three candidates with frame tags (curiosity / benefit / contrarian), winner, lift over the loser in percentage points, and a one-line gut take.
7. **Roll up monthly.** After roughly 12 sends, patterns stabilize. The Open/Click Analyst publishes a monthly roll-up showing which frame is winning in our niche this quarter; the founder reads it before the next editorial planning cycle.
8. **Feed winners back into the editorial calendar.** A winning frame repeats — the topic does not. The editorial-calendar skill consumes this signal.

## Outputs

- `analytics/subject-line-log.md` — append-only row per send: date, three candidates, frames, winner, lift, gut take.
- `analytics/subject-line-rollup/<YYYY-MM>.md` — monthly pattern report, founder-readable.
- A one-line into the Open/Click Analyst's weekly roll-up: this week's lift, the running quarter winner-frame.

## Anti-patterns

- Testing four or more candidates. Working memory breaks and the log stops yielding patterns.
- A/B testing on the paid tier. Paid subscribers expect consistency; we test on the free-to-paid path only.
- Testing subject lines that change the issue's actual angle. We test framings, not topics — otherwise the winner cannot inform future angles.
- Using ALL CAPS, fake `re:` prefixes, or fake forwards. Trust costs more than a four-point open-rate bump.
- Calling the winner on 30-minute opens. Early-opener skew makes the lift unreliable.
- Sending the winner to the holdout without the matching body. The lift was for the pair — if the body changes, the test is dead.
- Skipping the log entry "because the lift was small." Small lifts compound; missing rows break the monthly roll-up.

## Reference

Pair this skill with:
- `editorial-calendar` — winning frames flow back into angle selection.
- `paid-tier-conversion-funnel` — open rate is the upstream lever on every downstream conversion stage.
