---
schema: agentcompanies/v1
slug: programmatic-seo-at-scale
name: programmatic-seo-at-scale
description: 'Scope, build, and govern programmatic SEO programs that produce thousands of high-value pages without triggering thin-content or helpful-content penalties on the client domain.'
---

# programmatic-seo-at-scale

*How SEO Bureau ships programmatic SEO that survives helpful-content updates instead of inviting them — for marketplaces, directories, comparison sites, and multi-location templates.*

## When to load this skill

- A client has a structured dataset suited to programmatic pages (directories, marketplaces, comparison pages, location pages) and the audit identifies the opportunity.
- An existing programmatic template on a retainer client has been flagged for thin-content risk in the monthly white-label reporting pack.
- A recovery retainer kicks off after a helpful-content hit on an under-quality programmatic template.
- The content-strategist proposes a programmatic cluster during quarterly retainer planning.

## Inputs

- Approved cluster plan in `clients/<client-slug>/content/cluster-plan-v1.md` naming the programmatic entity.
- Keyword data validating real query demand at scale — at least 200 entity-level queries with non-trivial volume.
- Structured dataset audit: data source, ownership, freshness, accuracy, uniqueness.
- Template wireframe from the client's design system or our content-strategist.
- CEO sign-off on the rollout plan — programmatic always carries domain risk and never ships without it.

## Pre-flight checks

1. **Real query demand at scale.** Validate with keyword data, not gut feel. Reject if demand is thin.
2. **Unique, high-quality data.** Scraped, low-quality, or hallucinated data produces thin pages and risk. If the dataset is borrowed, the cluster is dead.
3. **Genuine value per page.** Each generated page must add at least one element competitors lack — proprietary data, embedded tools, real inventory, real reviews, real availability.
4. **Editorial layer plan.** Pure templating without any human-edited element is the helpful-content trap.
5. **Indexation budget.** Crawl-budget headroom must exist; if the site is already crawl-constrained, reduce or noindex elsewhere before scaling.

## Procedure

1. **Define the entity.** State the page in one sentence (e.g., "best CRM software for {industry} in {city}"). The entity drives the template.
2. **Template design.** Above the fold: unique value (data, tool, table). Body: explanation, supporting data, internal links. Below: schema, breadcrumbs, related entities. Hero LCP under 2.5s on mobile.
3. **Quality floor.** Per-page data-completeness threshold. Pages below the threshold are held or noindexed. The threshold is a column in the dataset, not a vibe.
4. **Schema.** Map appropriate types (`Product`, `LocalBusiness`, `ItemList`, `BreadcrumbList`, `FAQPage` only where genuine). Validate before launch.
5. **Phased indexation rollout.** Batches of 200–1,000, not 50,000 on day one. Monitor indexation rate, average position, and SERP performance before scaling.
6. **Weekly monitoring.** Indexation health, query expansion, CTR, helpful-content risk signals into the monthly white-label reporting pack as its own section.
7. **Governance loop.** Defined process for retiring, merging, or noindexing pages that underperform. Quarterly pruning is non-optional.

## Rollout decision matrix

| Signal | Action |
|--------|--------|
| Indexation rate >80%, CTR healthy | Scale the next batch |
| Indexation rate <40% after 4 weeks | Pause; investigate quality, internal links, crawl budget |
| Average position worsening after 6 weeks | Pause; rewrite template or prune underperformers |
| Manual action or helpful-content drop | Stop publishing; trigger algorithm recovery protocol |

## Outputs

- `clients/<client-slug>/content/programmatic/spec-v1.md` — entity, template, quality floor, schema map, rollout plan.
- `clients/<client-slug>/content/programmatic/governance.md` — pruning rules and quarterly review log.
- A programmatic section in the monthly white-label reporting pack.
- A CEO-signed rollout plan with go/no-go gates at 1K, 5K, and 25K published pages.

## Anti-patterns

- Generating pages from a template with no unique value per page.
- Mass-publishing 50,000 pages on day one. Indexation is earned in batches.
- Treating low-quality scraped data as "good enough" content.
- Ignoring the helpful-content update's bar for thin programmatic content.
- Skipping the quarterly governance pass because the cluster "is working" — until it isn't.
- FAQ schema on programmatic pages that are not actually FAQs.

## Reference

Pair this skill with:

- `content-brief-templates` for the editorial layer on hybrid templates.
- `schema-markup-implementation` for the entity schema layer.
- `algorithm-recovery-protocol` when a programmatic cluster takes a helpful-content hit.
