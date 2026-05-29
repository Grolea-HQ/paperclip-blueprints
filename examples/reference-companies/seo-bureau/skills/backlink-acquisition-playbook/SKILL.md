---
schema: agentcompanies/v1
slug: backlink-acquisition-playbook
name: backlink-acquisition-playbook
description: 'Run a white-hat link acquisition campaign — prospecting, qualification, outreach cadence, and link-velocity tracking — that protects the client domain and the retainer.'
---

# backlink-acquisition-playbook

*How SEO Bureau acquires editorial links under strict link-velocity discipline, without ever touching a PBN or a paid placement.*

## When to load this skill

- The CEO has approved a new link campaign on a retainer client.
- A new monthly retainer link cycle kicks off (default first Monday of the month).
- A recovery retainer requires fresh referring domains to rebuild authority after a link-spam diagnosis.
- The link-velocity tracker shows the client domain has fallen below its agreed referring-domain growth target for two consecutive months.

## Inputs

- Approved campaign brief signed off by the link-acquisition-lead and the CEO.
- Client's current link profile export and the active link-velocity tracker in `clients/<client-slug>/links/velocity-tracker.md`.
- Approved source list (no domain enters outreach until the CEO has signed off on the list).
- Outreach mailbox and inbox-warming status confirmed by the reporting-engineer.
- Anchor strategy aligned with the client's commercial query map.

## Procedure

1. **Brief.** Link-acquisition-lead writes `clients/<client-slug>/links/campaign-brief-v1.md`: client domain, target topics, link goals (count + DR range), anchor strategy, approved tactic mix, exclusion list. CEO approves before any prospecting.
2. **Prospect (60–80 domains).** Filter by topical relevance, organic traffic, Core Web Vitals health on the target page, and link-profile cleanliness. Reject anything flagged as a link farm, PBN, or thin-content directory.
3. **Qualify by hand.** Every prospect gets a hand-check. If a domain fails the smell test — sponsored-post mills, irrelevant verticals, declining traffic — it comes off the list. No exceptions, even when the campaign brief is hungry for volume.
4. **Approved tactic mix.** Pick from the approved list only:

| Tactic | When to use |
|--------|-------------|
| Digital PR (data stories, expert commentary) | Authority builds, brand sites, high-DR targets |
| Reactive pitches (HARO / Qwoted / Featured) | Daily volume, news cycles, fast wins |
| Resource-page outreach | Niche-relevant evergreen pages |
| Broken-link reclamation | Pages with verified 404s and clear replacements |
| Unlinked-mention reclamation | Brand mentions without hyperlinks |
| Pre-cleared editorial guest posts | Only on sites the editor has vetted; no link farms |
| Statistics + study citations | When the client owns proprietary research |

5. **Outreach cadence.** Personalize the first 1–2 sentences. Cap the sequence at three touches. One follow-up is fine; two is the ceiling. Anything past that damages the inbox reputation that the next campaign depends on.
6. **Track weekly.** Reporting-engineer updates `clients/<client-slug>/links/velocity-tracker.md` every Friday: prospects contacted, replies, placements, anchor distribution, DR profile, referring-domain delta MoM.
7. **Report monthly.** Client-reporting-manager pulls the link section into the white-label reporting pack on the 25th.

## Outputs

- `clients/<client-slug>/links/campaign-brief-v1.md` — CEO-approved campaign brief.
- `clients/<client-slug>/links/prospect-list-v1.csv` — qualified prospect list with disqualification reasons logged.
- `clients/<client-slug>/links/velocity-tracker.md` — running weekly tracker.
- The link section in the monthly white-label client report.

## Link-velocity discipline

A natural link profile grows steadily. Spikes look unnatural and trigger review. Keep new referring domains within a 20% MoM growth ceiling for established sites; greenfield domains can absorb faster growth, but the campaign brief must explicitly authorize it. Anchor distribution stays branded-heavy on commercial queries — over-optimized exact-match anchors are the fastest way to inherit a link-spam penalty.

## Anti-patterns

- Buying links and laundering them as "outreach" — instant retainer-ending behavior at SEO Bureau.
- Anchor-text over-optimization on commercial queries because the campaign brief had aggressive volume targets.
- Skipping CEO sign-off on the source list "to move faster" — the CEO sign-off is the link-safety gate.
- Mass-sending unpersonalized pitches to the entire prospect list. That is spam, not outreach.
- Letting the link-velocity tracker go stale for more than a week.
- Pitching domains the editor has never vetted because the prospect list ran low.

## Reference

Pair this skill with:

- `digital-pr-pitch-writing` for the data-story and reactive pitch layer.
- `algorithm-recovery-protocol` when running a post-link-spam rebuild.
- `white-label-reporting-pack` for the monthly link section.
