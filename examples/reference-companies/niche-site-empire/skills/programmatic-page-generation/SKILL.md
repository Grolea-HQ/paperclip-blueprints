---
schema: agentcompanies/v1
slug: programmatic-page-generation
name: programmatic-page-generation
description: 'Spin up large numbers of structured pages from a template plus dataset for long-tail capture at portfolio scale — without triggering thin-content penalties.'
---

# programmatic-page-generation

*How Niche Site Empire ships hundreds of long-tail pages without thin-content penalties — because programmatic SEO at portfolio scale is template × dataset, and the variance in the dataset is what separates a moat from a doorway page.*

## When to load this skill

- A cluster from `keyword-cluster-research` has a long-tail tail dense enough to template (e.g., "X for Y city", "X comparison Y", "X by spec Z") and the dataset is available.
- A Scale-verdict site has unused content capacity and a programmatic set has been proposed by the content-director.
- An existing programmatic set is being expanded with a new data column or geographic axis.
- A Helpful Content Update flags one of our programmatic sets as thin and we are deciding deindex vs. dataset-enrichment.

## Inputs

- Approved template signed off by content-director.
- Dataset with real variance — unique specs, locations, or comparison values per row.
- URL pattern validated by technical-seo-lead.
- Internal linking rules (every page links to cluster hero + 3-5 siblings).
- Schema requirements per page type (Product, FAQPage, BreadcrumbList).
- Affiliate disclosure block for affiliate-bearing programmatic pages.

## Procedure

1. **Template approval.** Content-director reviews and approves the template structure. The template itself is written by a human — we do not auto-generate templates with an LLM. The template contains placeholder variables for every dataset field.
2. **Dataset audit.** Confirm the dataset has real variance. If 80%+ of the page content would be identical across rows, the set is a doorway-page generator and must be rejected. Variance must be on the substantive axes (specs, prices, locations, methodology) — not just synonym swaps.
3. **URL + schema validation.** Technical-seo-lead validates the URL pattern, internal linking rules, and schema. JSON-LD blocks render once per page; FAQPage schema requires real FAQ content per row.
4. **Generation run.** Generate against the dataset into the site's CMS or static-site generator. Sitemap entries created at the same time. `lastmod` set to the generation date.
5. **5% sample read.** Editor + affiliate-disclosures-compliance pull 5% of generated pages at random and read them end-to-end. If they read as filler, kill the set before sitemap submission. Sample-read is the publishing gate.
6. **Sitemap submission.** Submit the new URL block to GSC. Tag the URL prefix in `portfolio/programmatic-sets.md`.
7. **30-day indexation watch.** seo-analyst tracks indexation rate, impression count, and click-through rate for 30 days. Sets below 40% indexation after 30 days trigger a dataset-variance review.

## Outputs

- `sites/<site-slug>/programmatic/<set-slug>/template.md` — the human-written template with variable placeholders documented.
- `sites/<site-slug>/programmatic/<set-slug>/dataset.csv` — the source dataset with variance audit notes.
- `sites/<site-slug>/programmatic/<set-slug>/sample-read.md` — the editor's read of the 5% sample with publish / kill verdict.
- `sites/<site-slug>/programmatic/<set-slug>/indexation-watch.csv` — 30-day indexation, impressions, CTR.
- An updated row in `portfolio/programmatic-sets.md` tracking the set across sites for portfolio-wide variance discipline.

## Anti-patterns

- Generating against a dataset with low variance ("best [product] in [city]" where only the city name changes). That is a doorway page set and Google deindexes them.
- Skipping the 5% sample read. Generated content rots silently if no one reads it; the sample is the only quality gate before sitemap submission.
- Auto-generating the template with an LLM. The template is the load-bearing artifact — a human writes it, the editor reviews it, the content-director signs off.
- Forgetting the affiliate disclosure on programmatic affiliate pages. Same compliance rules apply as editorial articles.
- Letting programmatic become 90% of a site's content. Programmatic supplements editorial; it does not replace it. The site's hub posts must still be hand-edited and authored.
- Orphan pages — generating without internal linking rules wired in. Orphans get deindexed within weeks.
- Re-running generation without re-validating schema. Template changes break schema silently.

## Reference

Pair this skill with:
- `keyword-cluster-research` for the upstream cluster the template serves.
- `schema-markup-implementation` for per-page schema validation.
- `eeat-author-bio-authoring` because programmatic pages need real bylines too.
