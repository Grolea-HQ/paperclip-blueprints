---
schema: agentcompanies/v1
slug: content-release-calendar
name: content-release-calendar
description: 'The Monday-09:00 weekly release rhythm that keeps content velocity steady, gives the Community Manager and CMO predictable promotion windows, and rotates template, guide, tool, and video slots across each month.'
---

# content-release-calendar

*One release per week, every week, every Monday. Steady content velocity beats bursty heroics — because the library compounds over time, not in a single drop.*

## When to load this skill

- It's Friday and the Writer or Video Producer needs to file next Monday's release for Content Director review.
- The Content Director is reviewing a request to swap a slot type (e.g. tool slot moving from week 3 to week 1).
- A slot is at risk of missing and the Content Director needs the recovery rule.
- Monday 09:00 is approaching and the release-readiness checklist needs to be confirmed.
- A new asset enters scope and needs a calendar slot before it can be promised externally.

## Inputs

- The current four-slot rotation (week 1 template, week 2 guide, week 3 tool, week 4 video).
- Owner availability for the assigned slot's pillar.
- The asset's INDEX.md, release-notes, Community Manager announcement copy, CMO promotion copy, and Member Success Lead "what changes for existing members" note — the five release-ready inputs.
- CEO approval for any slot-type swap (must be in advance, never morning-of).

## Procedure

1. **Friday before release.** Writer or Video Producer (whoever owns Monday's slot) files the source artifact with the Content Director. Content Director reviews, sends edits, signs off.
2. **Sunday end-of-day.** Community Manager has the announcement copy; CMO has the promotion copy; Member Success Lead has the one-line "what changes for existing members" note. If any are missing, the slot is not release-ready.
3. **Monday 09:00.** Release goes live in the library at the path defined by the asset-library-architecture skill.
4. **Monday 09:30.** Community Manager posts in the community space.
5. **Monday 12:00.** CMO promotes externally — email blast and social.
6. **Wednesday.** Member Success Lead scans member questions referencing the release and files any FAQ gaps back to the Content Director.
7. **Friday.** Next Monday's slot owner files their source artifact and the loop restarts.

## Slot ownership

| Week of month | Slot type | Primary owner |
|---|---|---|
| Week 1 | Template release | Template/Asset Designer |
| Week 2 | Long-form guide | Writer |
| Week 3 | Tool release | Tool Engineer |
| Week 4 | Video walkthrough | Video Producer |

The Content Director may swap slot types **in advance** with CEO approval. Never morning-of.

## Outputs

- `library/<type>/<category>/<asset-slug>/INDEX.md` and `release-notes.md` (one per Monday).
- A row in `analytics/release-log.md` capturing slot type, owner, on-time / slipped, and the Retention Analyst's "library count" tick.
- The community post (Community Manager), email blast (CMO), and social posts (CMO) — all sourced from the same release per the content-repurposing-pipeline skill.
- An entry in the weekly cohort report under "content velocity" so the goal of 50+ assets in 90 days has a visible burn-down.

## Anti-patterns

- Double-releasing on a single Monday to "catch up" after a miss — content velocity is steady, not bursty. A missed slot is reported, not back-filled.
- Swapping slot types on Monday morning to ship whatever is ready — slot rotation is a promise to the Community Manager and CMO who pre-write promotion.
- Promoting externally before community posts go live — members hear it from the community first, not from a tweet.
- Shipping a release without the INDEX.md / release-notes / community / promo / member-impact note assembled — incomplete releases break the back catalogue.
- Letting "week 5" of a five-Monday month default into a freelance slot — five-Monday months get a CEO decision on what type to ship, not a free-for-all.
- Treating a slipped slot as silent — it goes into the cohort report so the pattern is visible.

## Reference

Pair this skill with:
- `content-repurposing-pipeline` for how one release becomes five surfaces.
- `asset-library-architecture` for where the release lands on disk.
