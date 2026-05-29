---
schema: agentcompanies/v1
slug: editorial-calendar
name: editorial-calendar
description: 'Keeping four weeks of issue angles queued ahead of the fixed weekly send so the founder never wakes up to a blank page on send day and the cadence — our operating heartbeat — never slips.'
---

# editorial-calendar

*How Newsletter Press queues the next four issues so the send is sacred and the founder writes from a primed angle, not a cold one.*

## When to load this skill

- It is Monday morning and the Managing Editor is opening the weekly editorial review.
- The calendar has dropped to fewer than three rows in the future — that is the warning state.
- The founder records a voice memo with a candidate angle and it needs to be slotted.
- A subject-line winner from `analytics/subject-line-log.md` reveals a frame that should be repeated.
- A sponsor confirms placement for a date that needs an adjacent (not promotional) issue topic.
- The Staff Writer asks "what am I researching this week?"

## Inputs

- `editorial/calendar.md` — the canonical queue. Authoritative; one row per issue.
- Founder voice memos from the past seven days, transcribed and tagged in `editorial/founder-memos/`.
- The subject-line log — winning frames repeat in our niche.
- The reader-reply log — top three threads from the last two issues.
- The sponsorship schedule (which issues already have a sponsor slot booked).
- The voice guide at `editorial/voice-guide.md` — angles get rejected here if they cannot be written on-voice.

## Procedure

1. **Read the queue.** Open `editorial/calendar.md`. Count rows beyond today. If fewer than four, the priority of this session is refill, not optimization.
2. **Source candidate angles from four buckets, in priority order.**
   - Founder voice memos (highest weight — voice-checked at source).
   - Reader replies to past issues (proven engagement signal).
   - Subject-line winners from the rolling log (frame, not topic).
   - Sponsor-adjacent topics — adjacent, never promotional. A fintech sponsor does not buy a fintech issue.
3. **Score each candidate against three filters.**
   - Can the founder write this in one draft block? (If no, defer.)
   - Does it sit inside the founder's stated coverage scope? (If no, decline.)
   - Is the angle distinct from the last four sends? (If no, hold for two more weeks.)
4. **Fill the table.** One row per issue, four weeks out. The table format is fixed:

| Send date | Working title | Angle | Founder draft due | Editor due | Producer due |
|---|---|---|---|---|---|

5. **Notify downstream owners.** Staff Writer, Research Analyst, and Newsletter Producer read the calendar Monday by 11:00. The Managing Editor pings only on changes.
6. **Escalate to the CEO if the calendar cannot be refilled to four rows.** Empty is better than off-voice, but two weeks is the floor — below that, the cadence is at risk.

## Outputs

- `editorial/calendar.md` — always four rows ahead by close of Monday review.
- `editorial/founder-memos/<YYYY-MM-DD>-<slug>.md` — transcribed voice memos with the angle tagged.
- A status line in the Managing Editor's weekly roll-up: rows ahead, candidates in reserve, gaps the CEO needs to fill.

## Anti-patterns

- Letting the calendar drop to fewer than two weeks. That is a cadence-at-risk state — escalate, do not paper it.
- Filling slots with topics the founder has not voice-checked. Empty is better than off-voice, because off-voice sends erode the moat we are paid for.
- Treating sponsor-paid issues as editorial. The masthead does not rent.
- Slotting four sequential issues on the same theme. Coverage exhaustion is a churn driver — `cohort-churn-tracking` traces it back here.
- Promoting a subject-line winner topic into another full issue. Repeat the frame, not the topic.
- Re-running an angle the founder has already published in the last 90 days unless they explicitly ask for a follow-up.

## Reference

Pair this skill with:
- `newsletter-voice-capture` to reject off-voice candidates at the calendar stage, before any drafting happens.
- `subject-line-ab-testing` for the frame-vs-topic distinction that drives angle reuse.
