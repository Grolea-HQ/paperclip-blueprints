---
schema: agentcompanies/v1
slug: schema-markup-implementation
name: schema-markup-implementation
description: 'Plan, scope, and validate structured-data implementations across client templates to earn SERP features and clearer entity signals — without inviting structured-data manual actions.'
---

# schema-markup-implementation

*How the schema-implementation-specialist and tech-seo-lead plan, ship, and maintain JSON-LD schema that produces SERP features instead of policy violations.*

## When to load this skill

- The technical SEO audit identifies missing or broken schema on priority templates.
- A new ongoing-retainer client enters onboarding and the Phase 1 baseline includes a schema audit.
- A recovery sprint follows a SERP-feature loss (FAQ rich result, sitelinks search box, Product result).
- A new template ships in the client's CMS and the editorial layer requests schema coverage.
- GSC Rich Results flags a warning/error spike across a template.

## Inputs

- Read access to the client CMS so field mappings trace to real data sources.
- A list of templates in scope (homepage, category, product, article, location, FAQ).
- Existing schema export from a fresh crawl with JS rendering enabled.
- Rich Results Test and Schema.org validator runs on representative URLs per template.
- CEO sign-off on policy-adjacent types (FAQ, HowTo, Review) — schema misuse is one of the fastest paths to a manual action.

## High-leverage schema types

| Type | When to use | SERP outcome |
|------|-------------|--------------|
| `Organization` | Site-wide | Entity signals, knowledge panel eligibility |
| `WebSite` + `SearchAction` | Site-wide | Sitelinks search box |
| `BreadcrumbList` | Every template | Breadcrumb display in SERP |
| `Product` + `Offer` + `AggregateRating` | E-commerce product pages | Price, availability, rating in SERP |
| `Article` / `NewsArticle` | Editorial | Top Stories, rich result eligibility |
| `FAQPage` | Pages that genuinely answer 3+ FAQs | FAQ rich result (where still served) |
| `HowTo` | Step-by-step instructional pages | HowTo rich result |
| `VideoObject` | Pages with embedded video | Video carousel eligibility |
| `LocalBusiness` (subtype) | Local SEO clients per location | Map Pack and local pack eligibility |

## Procedure

1. **Audit existing schema.** Run Rich Results Test and Schema.org validator. Catalog every type in use and every validation error in `clients/<client-slug>/audits/schema-audit-v1.md`.
2. **Map templates to types.** For each in-scope template, name the schema types that apply and the CMS field each binds to. No hardcoded values.
3. **Scope dev work.** Produce a developer-ready spec — JSON-LD examples per template, required CMS fields, edge cases, validation criteria. Output: `clients/<client-slug>/audits/schema-spec-v1.md`.
4. **Implementation handoff.** Client's dev team ships the work. SEO Bureau briefs and validates — we do not own publishing.
5. **Validate every template post-implementation.** Errors must be fixed before sign-off; warnings reviewed case by case.
6. **Monitor.** Track Rich Results performance in GSC. Tie schema deployment to SERP-feature wins or losses in the monthly white-label reporting pack.
7. **Maintain.** Quarterly validation prevents silent drift when the CMS changes.

## JSON-LD example (Product)

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "{{ product.name }}",
  "sku": "{{ product.sku }}",
  "brand": { "@type": "Brand", "name": "{{ product.brand }}" },
  "offers": {
    "@type": "Offer",
    "price": "{{ product.price }}",
    "priceCurrency": "{{ product.currency }}",
    "availability": "{{ product.availability_schema }}"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "{{ product.rating_value }}",
    "reviewCount": "{{ product.review_count }}"
  }
}
```

## Outputs

- `clients/<client-slug>/audits/schema-audit-v1.md` — audit and findings.
- `clients/<client-slug>/audits/schema-spec-v1.md` — dev-ready spec with JSON-LD and CMS bindings.
- A Rich Results section in the monthly white-label reporting pack.
- `clients/<client-slug>/audits/schema-review-<yyyy-q>.md` — quarterly health review.

## Anti-patterns

- Marking up FAQ schema on pages that are not actual FAQs.
- Stuffing review schema where reviews are not present.
- Hardcoding schema values instead of binding to CMS fields — the schema goes stale the moment the CMS changes.
- Treating schema as a one-time task; CMS migrations and plugin updates silently break it.
- Recommending HowTo or FAQ markup the client cannot maintain.
- Skipping the Rich Results Test post-deploy because "it validated in dev".

## Reference

Pair this skill with:

- `technical-seo-audit` for the broader template audit.
- `local-seo-audit` for `LocalBusiness` per-location implementations.
- `gsc-ga4-reporting-dashboard` to tie schema deploys to SERP-feature wins.
