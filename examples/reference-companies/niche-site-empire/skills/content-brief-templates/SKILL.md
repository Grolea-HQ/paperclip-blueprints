---
schema: agentcompanies/v1
slug: content-brief-templates
name: content-brief-templates
description: 'Author content briefs that let writers ship autonomously — cluster, intent, structure, product list, internal links, schema, and disclosures, all locked before drafting starts.'
---

# content-brief-templates

*How Niche Site Empire writes briefs complete enough that writers ship without questions — because the autonomous content rail only works if the brief is the contract.*

## When to load this skill

- A keyword cluster has been scored and approved by the content-director and a brief is needed before any draft starts.
- A refresh has been queued and the writer needs an updated brief reflecting the new SERP and product list.
- A programmatic page set has cleared its sample-read and the editor wants to back-fill an editorial hub article around the cluster.
- A writer comes back with a question mid-draft — that is a signal the brief was incomplete and this skill is reloaded to fix it.

## Inputs

- Cluster brief from `keyword-cluster-research` (hero keyword, supporting keywords, intent, target site).
- Top-3 ranking articles for the hero keyword, read and summarized for SERP context.
- Affiliate-program-manager's product list with verified affiliate links (commercial briefs only).
- Internal linking targets — 4-8 specific URLs on the target site that the new article must link to.
- Author assignment from the site's named author roster (no anonymous bylines, no "editorial team").

## Procedure

Every brief contains exactly these eleven sections, in this order, with no exceptions. A brief missing any section is rejected by the editor before it reaches the writer.

1. **Target site + cluster.** Which portfolio site, which keyword cluster, which sub-position in the cluster (hero / supporting / FAQ).
2. **Hero keyword + primary intent.** Example: "best electric pruners for arthritis" — commercial intent.
3. **Supporting keywords.** Bullet list of 5-15 long-tail variants the article must cover.
4. **Target word count.** Range, not a single number (e.g., 2,200-2,800 words for a commercial roundup; 1,400-1,800 for an informational explainer).
5. **Structure outline.** Full H2/H3 outline, including required sections: intro, comparison table, individual product reviews, buying guide, FAQ.
6. **SERP context.** Top-3 ranking articles + the gap we are filling. Writer reads these before drafting.
7. **Product list (commercial).** Affiliate-program-manager picks the products and supplies affiliate links. Writer never picks products.
8. **Internal linking targets.** 4-8 internal links to specific URLs on the site, with anchor-text suggestions.
9. **Schema requirements.** Product, FAQPage, BreadcrumbList — which apply and which fields are required.
10. **Author assignment.** Real, named author from the site's roster. Byline is locked before draft starts, not assigned after.
11. **Affiliate disclosure block.** Confirmed by affiliate-disclosures-compliance — exact copy and placement.

A brief explicitly excludes vibes ("make it engaging"), personality requests ("add humor"), and open-ended questions for the writer. If we do not know the answer at brief time, the brief is not ready.

## Outputs

- `sites/<site-slug>/briefs/<slug>-brief.md` — the complete brief, ready for the writer, with all 11 sections filled.
- An updated row in `sites/<site-slug>/editorial-calendar.md` linking brief → writer → due date → publish slot.
- A check-in entry in the editor's queue, scheduled for 48 hours after assignment.

## Anti-patterns

- Writers picking their own products on commercial articles. Product selection is locked at brief time by the affiliate-program-manager so EPC math holds.
- Briefs without a SERP-context section. Writers waste hours recreating what already ranks instead of filling the gap.
- Briefs without internal linking targets. Articles ship orphaned, hurt cluster authority, and trigger our internal-link audit.
- "Editorial team" or anonymous bylines. E-E-A-T requires named, accountable authors per article.
- Briefs with open questions for the writer. If the editor cannot answer it, the writer cannot either; close the question before assigning.
- Briefs that skip the schema section. Schema is a publishing gate; missing it blocks the publish.

## Reference

Pair this skill with:
- `keyword-cluster-research` for the upstream cluster input.
- `eeat-author-bio-authoring` for the named-author roster the brief draws from.
- `schema-markup-implementation` for the schema section detail.
