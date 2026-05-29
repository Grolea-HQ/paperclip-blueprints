---
schema: agentcompanies/v1
slug: content-brief-templates
name: content-brief-templates
description: 'Turn approved keyword clusters into productized content briefs that writers and editors can ship without ambiguity — pillar, supporting article, and product-led variants.'
---

# content-brief-templates

*How SEO Bureau converts a CEO-approved content cluster plan into briefs writers can execute against and editors can hold accountable.*

## When to load this skill

- A new content cluster plan has been signed off by the CEO during onboarding or a quarterly retainer review.
- The editor or seo-writer requests a brief for a queued cluster slot.
- A retainer with content scope flags a brief shortage in the monthly white-label reporting cycle.
- A recovery sprint requires rewriting thin or AI-pattern content flagged by the helpful-content diagnosis.

## Inputs

- Approved `clients/<client-slug>/content/cluster-plan-v1.md` with pillar, siblings, target queries.
- SERP analysis for the primary query: top 10 results, dominant content types, average word count, common subheadings, PAA queries, SERP-feature observations.
- Client brand voice notes from `clients/<client-slug>/content/voice-v1.md`.
- Internal-link inventory: pillars, cluster siblings, product/category pages.

## Procedure

1. **Pull SERP analysis** for the primary query. Capture dominant content types, average word count, common subheadings, PAA coverage, SERP-feature opportunities.
2. **Identify the angle gap.** One sentence: what the top 10 results miss or do badly. If you cannot find a gap, escalate to the content-strategist before drafting.
3. **Fill the template** below in `clients/<client-slug>/content/briefs/<slug>.md`. Brief length: 600–1,200 words. Target article: 1,500–3,500 words.
4. **Editor reviews the brief** before assignment to the seo-writer. Editor signature lives in the brief frontmatter.
5. **Brief enters the production queue.** Writer ships the draft; editor passes it against the Definition of Done.

## Brief template (every brief)

1. **Target query + intent.** Primary keyword, search intent (informational / navigational / transactional / commercial), SERP type observed (featured snippet, video, PAA, Top Stories).
2. **Audience snapshot.** Who is searching, what stage of awareness, what they already know, what they need to do next.
3. **Angle.** One-sentence point of view that differentiates the piece from the top 10 SERP results.
4. **Structure.** H1, H2/H3 outline. Word-count target. Visuals required (screenshots, diagrams, custom charts, embedded calculators).
5. **Internal links.** 3–7 specific internal targets — pillar, cluster siblings, product or category pages — with the recommended anchor for each.
6. **External references.** 2–5 authoritative sources to cite. No direct competitor links unless explicitly approved.
7. **Schema.** Which schema types to mark up (Article, FAQ, HowTo, Product) and the FAQ candidates flagged inline.
8. **Core Web Vitals notes.** Image weight ceiling, hero-image LCP requirement, any embeds that risk INP or CLS regressions.
9. **Definition of done.** Acceptance criteria the editor checks before approval — angle delivered, internal links present, schema flagged, brand voice respected, no AI-pattern filler.

## Brief variants

| Variant | When to use | Differences from the base template |
|---------|-------------|------------------------------------|
| Pillar | Pillar pages anchoring a cluster | Longer outline (3,500+ words), 7–10 internal links, Article + FAQ schema |
| Supporting article | Cluster siblings | Standard 1,500–3,500 words, 3–5 internal links |
| Product-led | Transactional intent | Tight angle, Product + Offer + AggregateRating schema, fewer external links |

## Outputs

- `clients/<client-slug>/content/briefs/<slug>.md` — editor-approved brief, referenced in the writer's task.
- An entry in the monthly content production tracker tied to the white-label reporting pack.

## Anti-patterns

- Briefs that are keyword lists with no angle.
- Briefs that prescribe word count but skip structure — that produces filler.
- Briefs that ask the writer to "be creative". A brief that does not name the angle has not done its job.
- Letting AI-generated outlines pass without editor review — helpful-content updates exist because of exactly this pattern.
- Briefs that ignore the internal-link inventory and ship orphaned articles.
- Briefs that prescribe schema the page is not eligible for.

## Reference

Pair this skill with:

- `programmatic-seo-at-scale` when the cluster slot is a template, not a one-off.
- `schema-markup-implementation` for the schema field of each brief.
- `gsc-ga4-reporting-dashboard` for measuring brief-to-traffic conversion.
