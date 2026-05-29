---
schema: agentcompanies/v1
slug: digital-pr-pitch-writing
name: digital-pr-pitch-writing
description: 'Write digital PR pitches journalists actually open, read, and place — data hooks, angle development, and pitch structure that produce editorial links inside the link-velocity discipline.'
---

# digital-pr-pitch-writing

*How the digital-pr-specialist writes pitches that produce editorial links on tier-1 publications without trade-press spam patterns.*

## When to load this skill

- A new digital PR campaign has been approved by the CEO with a target referring-domain count and DR profile.
- The link-acquisition-lead has signed off on a data study or original research ready to pitch.
- A reactive opportunity (breaking news, trending topic, viral data point) is live and the pitch must ship inside 24 hours.
- The link-velocity tracker shows the campaign trailing its target and the pitch pipeline needs refilling.

## Inputs

- Approved campaign brief from `clients/<client-slug>/links/campaign-brief-v1.md`.
- The underlying data asset (study, dataset, embedded chart, expert quote) hosted at a stable, ungated URL.
- Journalist target list scoped to writers who have published adjacent stories in the last 12 months — no generic `press@` inboxes.
- Embargo terms and asset bundle (charts, raw data, expert sources, headshots) if the pitch is embargoed.
- Approved anchor strategy so the placement contributes to link-velocity discipline rather than over-optimizing commercial queries.

## Procedure

1. **Angle development.** Start from the data, not the company. The story is the angle; the link is the byproduct. Write the angle as a one-sentence claim a journalist could file under their own byline.
2. **Journalist targeting.** Build a 30–60 list of named journalists with adjacent bylines inside 12 months. Reject generic `press@` inboxes and contacts without verifiable recent work.
3. **Draft using the pitch anatomy** below. Plain prose. No marketing language. No "groundbreaking", no "revolutionary".
4. **Review.** Link-acquisition-lead reviews every pitch before send. CEO approves the angle for high-stakes campaigns (national tier-1, regulated verticals, recovery rebuilds).
5. **Send and follow up.** Send during the journalist's local morning. One follow-up max, 5 business days later. Two damages mailbox deliverability for the next campaign.
6. **Track.** Log pitches, opens, replies, placements, links, and anchor types into `clients/<client-slug>/links/digital-pr-tracker.md`. Reporting-engineer pulls placements into the monthly white-label reporting pack.

## Pitch anatomy

1. **Subject line.** 6–10 words. Lead with the data point or the angle, not the company. Pass the "would a journalist click this in their 400-email inbox" test.
2. **First sentence.** Why this story, why this journalist, why now. No corporate throat-clearing.
3. **The hook.** The single most surprising data point or angle. One sentence.
4. **Context.** Two to three sentences that frame the hook and offer a quote or chart.
5. **What's available.** Embargo terms (if any), assets, expert sources, raw data link.
6. **Sign-off.** Real human name, real phone number, link to the press kit or data page.

## Example subject lines

| Worse | Better |
|-------|--------|
| New study from Acme Inc. on remote work | Remote workers are 23% more likely to skip lunch — data |
| Acme launches Q3 industry report | Q3 data: tech hiring fell in 7 of 10 US metros |
| We have data on inflation | Grocery prices climbed fastest in cities with no rail transit |

## Outputs

- `clients/<client-slug>/links/digital-pr-tracker.md` — campaign log.
- `clients/<client-slug>/links/pitches/<campaign-slug>/<journalist>.md` — approved pitch drafts.
- Placements feeding the link section of the monthly white-label reporting pack.

## Anti-patterns

- Pitching a company milestone as if it were a story. Funding rounds and product launches are not journalism.
- Mass-sending the same pitch to 200 journalists. Personalize the first 1–2 sentences or do not send.
- Hiding the data behind a gated download — journalists will not chase a form.
- Sending an embargoed pitch without a hard embargo time and confirmation contact.
- Skipping the link-acquisition-lead review because the campaign feels routine.
- Following up twice. The second follow-up costs more than the link is worth.

## Reference

Pair this skill with:

- `backlink-acquisition-playbook` for the campaign-brief, prospecting, and tracking layer.
- `white-label-reporting-pack` for the link section in the monthly report.
- `algorithm-recovery-protocol` when the campaign is part of a recovery sprint.
