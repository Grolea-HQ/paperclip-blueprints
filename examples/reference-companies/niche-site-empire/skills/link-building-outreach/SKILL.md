---
schema: agentcompanies/v1
slug: link-building-outreach
name: link-building-outreach
description: 'Earn editorial links via HARO pitches, digital PR data stories, and resource-page outreach — never paid links, never PBNs, never reciprocal trades.'
---

# link-building-outreach

*How Niche Site Empire earns editorial links without paying for them — because paid links are a guideline violation, manual-action risk, and incompatible with our long-game portfolio economics.*

## When to load this skill

- A Scale-verdict site has been allocated a quarterly link budget and needs a campaign plan.
- A digital PR data story is being commissioned and the outreach list needs building.
- A HARO query lands that matches one of our portfolio sites' authority topics.
- Penalty-recovery flags weak link velocity as a contributing factor.
- A new site needs its first 10 earned links before being submitted to Mediavine.

## Inputs

- Site URL, authority topics, and named author roster (HARO requires a real source).
- Approved digital PR budget and topic (CEO signs off on data-story themes).
- Active HARO / Connectively / Qwoted account for the relevant niche categories.
- Outreach CRM (e.g., Pitchbox or a tracked spreadsheet) with response and placement metrics.
- A real, credentialed author from `eeat-author-bio-authoring` available as the named source for pitches.

## Procedure

### Channel 1: HARO (Help a Reporter Out / Connectively / Qwoted)

- Monitor queries 3x daily on weekdays: 08:00, 13:00, 17:00 local.
- Filter for queries matching one of the portfolio sites' authority topics.
- Pitch within 4 hours of the query landing — journalists fill the source slot fast and late pitches are ignored.
- Pitch format: 80-150 word answer, named source (real author with verifiable credentials), one quote-ready sentence, contact info.
- Target pitch-to-placement rate: 15%+. Below 10%, refine the topic filter — we are pitching off-topic queries.

### Channel 2: Digital PR data stories

- One data story per Scale-verdict portfolio site per quarter.
- Topic: an angle that journalists will actually cover — industry survey, trend analysis, geographic comparison, original methodology.
- Wrap as a press release plus media kit: chart, named quote, methodology summary, embargo date if relevant.
- Pitch to 30-50 outlets directly. Target 5-10 placements per campaign.
- Re-pitch the story 4-6 weeks later to outlets that did not respond — story angles age into newsworthy slots.

### Channel 3: Resource-page outreach

- Find resource pages via Google operators: `inurl:resources "topic"`, `intitle:"resources" "topic"`, `"useful links" "topic"`.
- Pitch one specific piece of content that fits the page's existing structure — not "please link to my site".
- Expect a low conversion rate (3-5%); volume compensates.

## Outputs

- `portfolio/link-campaigns/<campaign-slug>/pitch-list.csv` — outlets, contacts, pitch status, follow-up dates.
- `portfolio/link-campaigns/<campaign-slug>/placements.md` — every earned link with anchor text, publish date, and the article that received the link.
- `sites/<site-slug>/link-profile/earned-links.csv` — append-only ledger of every earned link, used for the quarterly authority-site-audit.
- A weekly HARO pitch log with pitch count, placement count, and pitch-to-placement rate by author.

## Anti-patterns

- Buying links. Ever. Manual-action risk and a permanent stain on the site's link profile.
- Running PBNs. Ever. Detection is a matter of when, not if.
- Trading links in 1:1 reciprocal patterns ("link to me, I'll link to you"). Google treats reciprocal patterns as a scheme.
- Comment-spam blogs or low-quality directory submissions. Pointless, tarnishing, and manual-action risk.
- Pitching every HARO query indiscriminately. Journalists blacklist spam-pitchers and the entire portfolio takes the hit.
- Skipping the named-source requirement. Anonymous pitches get rejected by every credible outlet.
- Treating link quantity as the metric. One link from a real publication beats 50 from low-DA blogs — quality compounds, quantity does not.
- Pitching without a real, credentialed author behind the quote. The source is the offer; the quote is the artifact.

## Reference

Pair this skill with:
- `eeat-author-bio-authoring` because every HARO pitch needs a real named source.
- `penalty-recovery-protocol` when link-profile rebuilds are part of a recovery campaign.
- `authority-site-audit` because the link-profile module pulls directly from this skill's outputs.
