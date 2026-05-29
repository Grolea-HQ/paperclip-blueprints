---
schema: agentcompanies/v1
slug: eeat-author-bio-authoring
name: eeat-author-bio-authoring
description: 'Author bios and article-level E-E-A-T signals that satisfy Google''s quality raters — real authors, verifiable credentials, Person schema, named bylines.'
---

# eeat-author-bio-authoring

*How Niche Site Empire builds the Experience, Expertise, Authoritativeness, and Trustworthiness signals that separate a portfolio site from a content farm in Google's eyes — because YMYL-adjacent queries do not rank without them.*

## When to load this skill

- A new portfolio site is launching and needs its initial roster of 2-5 named authors before the first article publishes.
- An author is being added to an existing site (recruited contributor, subject-matter expert, or staff writer).
- A penalty-recovery campaign flags weak author signals as a likely contributor to a Helpful Content Update drop.
- A YMYL-adjacent cluster (health, finance, legal, parenting) is being briefed and needs a credentialed "Reviewed by" expert assigned.
- Quarterly audit surfaces articles with anonymous or "editorial team" bylines that must be reassigned.

## Inputs

- The author's real name, real photo (not AI-generated, not stock), and verifiable credentials.
- External profile links: LinkedIn, Twitter/X, personal site, or published work elsewhere.
- Domain experience claim (e.g., "Certified arborist", "Tested 80+ pruners over 3 years").
- Site template access for bio page, byline component, and author archive page.
- Person schema template from `schema-markup-implementation`.

## Procedure

1. **Verify the author exists.** Reverse image search the photo. Confirm at least two external profile links resolve to the same person. If the author exists nowhere else on the web, the signal is too weak — reject the addition.
2. **Confirm credentials.** Every credential in the bio must be verifiable. "Certified arborist" requires a certifying body. "Tested 80+ pruners" requires either a published methodology or original test photos we host on the site.
3. **Build the bio page.** Each site has a `/authors/<author-slug>/` page with: full credentials, headshot, Person schema (linked to external profiles via `sameAs`), and a dynamic list of articles authored.
4. **Wire the byline.** Every article on the site carries a byline above the fold linking to the bio page. Programmatic pages get bylines too — no exceptions.
5. **Wire the author archive.** The bio page lists every article the author has published, ordered by publish date. This is the authority-trail Google's quality raters check.
6. **Assign YMYL reviewers.** For health, finance, legal, or parenting clusters, assign a credentialed "Reviewed by" expert per article. The reviewer's credentials must outrank the author's on the YMYL axis.
7. **Audit cadence.** Quarterly, alongside the authority-site-audit, verify every author still has live external profiles and that no articles have slipped to anonymous bylines.

## Outputs

- `sites/<site-slug>/authors/<author-slug>/bio.md` — full bio copy with credentials, photo path, external links, and Person schema block.
- `sites/<site-slug>/authors/roster.md` — current named author roster for the site, used by `content-brief-templates` to assign bylines.
- `sites/<site-slug>/authors/<author-slug>/articles.md` — generated list of articles authored, used for the author archive page.
- A Person schema JSON-LD snippet validated against Google's Rich Results Test.

## Anti-patterns

- Spinning up fake author profiles with stock or AI-generated photos. Reverse image search exposes this in minutes and burns the site's trust signal permanently.
- AI-generated bios with vague filler ("X is passionate about gardening and loves writing about plants"). Useless to Google's quality raters — bios need verifiable specifics.
- One catch-all "editorial team" byline across the site. Quality raters specifically look for named, accountable authors per article.
- Bios without external verification. If the author exists nowhere else on the web, the E-E-A-T signal is weak and Google discounts it.
- Skipping Person schema on bio pages. Easy win, often missed.
- Forgetting bylines on programmatic pages. Programmatic supplements editorial; both need real authors.
- Letting the author archive break when an author leaves. Dead links signal abandonment.

## Reference

Pair this skill with:
- `schema-markup-implementation` for the Person schema details and `sameAs` wiring.
- `content-brief-templates` because every brief draws the byline from the author roster this skill maintains.
- `penalty-recovery-protocol` when weak author signals are flagged as a recovery target.
