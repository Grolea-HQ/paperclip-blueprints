---
schema: agentcompanies/v1
slug: schema-markup-implementation
name: schema-markup-implementation
description: 'Deploy and validate JSON-LD schema across the portfolio — Article, Product, FAQPage, BreadcrumbList, HowTo, Person, Organization — without triggering rich-result manual actions.'
---

# schema-markup-implementation

*How Niche Site Empire deploys and validates structured data across the portfolio — because schema is rich-result fuel, but spammy or mismatched markup triggers manual actions faster than almost any other quality issue.*

## When to load this skill

- A new portfolio site is launching and needs its sitewide schema stack configured.
- A new article type (review, comparison, FAQ, how-to) is being templated and needs its schema block defined.
- A template change has just shipped and pages using it need re-validation against Google's Rich Results Test.
- A manual action arrives citing structured-data violations and the affected pages need an emergency audit.

## Inputs

- The site's CMS or static-site generator template files.
- Current schema plugin configuration (Rank Math, Yoast, or hand-injected templates).
- Article inventory by type — editorial article, product review, comparison, FAQ-bearing, how-to.
- Author roster from `eeat-author-bio-authoring` for Person schema wiring.
- Google's Rich Results Test access for validation.

## Procedure

### The portfolio standard

Every site emits, sitewide:

- `Article` or `BlogPosting` schema on every editorial article.
- `Product` schema on every product review or comparison page, with `aggregateRating` only when the review actually contains a rating.
- `FAQPage` schema where the article has a real FAQ section (3+ Q/A pairs visible on the page).
- `BreadcrumbList` schema sitewide.
- `Organization` + `WebSite` schema on the homepage.
- `Person` schema linked to author bio pages, with `sameAs` to external profiles.

### Implementation rules

1. **JSON-LD only.** No microdata, no RDFa.
2. **Plugin or template.** Rank Math / Yoast where possible. Hand-injected only when the plugin cannot express the schema — reviewed by technical-seo-lead before merge.
3. **Per-publish validation.** Every published article validated against Google's Rich Results Test. No publication if validation fails — hard publishing gate.
4. **Re-validation on template change.** Any template change re-runs validation across 20 sample articles before sitewide ship.
5. **No markup of content not on the page.** Review snippets without visible reviews, aggregateRating without on-page rating — all violations.

### Schema-by-page-type quick reference

- Editorial article: Article + BreadcrumbList + Person.
- Product review (single product): Article + Product + Person + Review + BreadcrumbList.
- Comparison roundup: Article + BreadcrumbList + Person. No Review schema — Google requires individual review pages.
- FAQ-bearing article: add FAQPage schema if 3+ Q/A pairs are visible.
- How-to: HowTo schema only on genuinely how-to content. Deprecated on commercial pages.

## Outputs

- `sites/<site-slug>/schema/standard.md` — the per-site schema standard, listing which schemas apply to which page types.
- `sites/<site-slug>/schema/validation-log.csv` — per-publish validation results, append-only, used by the technical audit.
- `sites/<site-slug>/schema/template-snippets/` — the JSON-LD snippets for each template type, version-controlled.
- An updated row in `portfolio/schema-coverage.md` showing each site's schema coverage rate by page type.

## Anti-patterns

- Shipping schema that does not reflect on-page content. This is the #1 cause of structured-data manual actions across the portfolio.
- Using `HowTo` schema on commercial product pages. Google deprecated rich-result eligibility for this pattern; markup is wasted at best, manual-action risk at worst.
- Stacking `aggregateRating` on FAQPage. Rich-result violation.
- Adding `Review` schema to a roundup post. Google requires individual review pages, not lists.
- Forgetting to re-validate after a template change. Template-driven schema breaks silently across hundreds of pages at once.
- Skipping `BreadcrumbList` sitewide. Easy win, often missed.
- Marking up ratings that were never on the page. Inflated ratings are the fastest path to a manual action.
- Letting schema drift between plugin and hand-template. Pick one source of truth per schema type.

## Reference

Pair this skill with:
- `eeat-author-bio-authoring` for Person schema wiring on bio pages.
- `programmatic-page-generation` for schema validation on generated sets.
- `authority-site-audit` because the technical-audit module pulls schema coverage from this skill's outputs.
