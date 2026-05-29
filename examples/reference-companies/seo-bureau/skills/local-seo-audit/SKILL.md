---
schema: agentcompanies/v1
slug: local-seo-audit
name: local-seo-audit
description: 'Scope and ship a local SEO audit for single-location or multi-location SMB and mid-market clients — Google Business Profile, citations, locality signals, review profile, and Map Pack visibility.'
---

# local-seo-audit

*How SEO Bureau audits clients whose organic traffic depends on Map Pack visibility, locality signals, and the Google Business Profile ecosystem.*

## When to load this skill

- An audit-tier engagement ($4K–$8K) includes a local component (multi-location retail, services, healthcare, hospitality).
- A multi-location retainer client requests a per-location diagnosis ahead of a quarterly review.
- The client has lost Map Pack visibility for priority queries inside the last 30 days.
- A new ongoing-retainer client with a local footprint enters onboarding and the baseline audit must include locality signals.

## Inputs

- Owner-confirmed Google Business Profile access (or verified read access for every location).
- Citation-audit tooling — BrightLocal, Whitespark, or equivalent — provisioned for the client account.
- Client's full location list with addresses, phone numbers, hours, categories, and service-area definitions.
- Verified GSC + GA4 access from onboarding so the audit ties to organic traffic, not just rankings.
- Local competitor set (top 3 per location) named by the account-manager.

## Procedure

1. **Google Business Profile audit.** One row per location. Capture categories, services, attributes, photos, posts, Q&A, review profile, messaging, and product feeds. Output to `clients/<client-slug>/audits/local/gbp-<location>.md`.
2. **Citation audit.** NAP (name, address, phone) consistency across the top 25 citation sources for the client's vertical. Flag inconsistencies with source URL and the corrected value.
3. **On-page locality signals.** Local schema (`LocalBusiness`, `Place`, `GeoCoordinates`), location-page structure, internal linking from city/region pillar pages, hreflang where multilingual.
4. **Review profile.** Volume, recency, rating distribution, response rate, response quality. Compare against top 3 local competitors per location.
5. **Local SERP analysis.** Map Pack visibility for priority queries across a representative grid (5x5 or 7x7 per location). Identify rank-blocking factors: category mismatch, proximity, review weight, primary-category dilution, spam listings.
6. **Local content gaps.** City/region pages, neighborhood content, locally relevant editorial. Flag thin or duplicative location pages.
7. **Core Web Vitals on location templates.** LCP, INP, CLS per location template; image-weight regressions and embedded-map INP issues are the usual suspects.
8. **Prioritized recommendations.** Rank by traffic impact x effort. Multi-location clients get a global section plus a per-location section.

## What "good" looks like per section

| Section | Bar to clear |
|---------|--------------|
| GBP completeness | All categories chosen correctly, photos refreshed quarterly, posts within last 30 days, Q&A monitored |
| NAP consistency | Zero inconsistencies in the top 25 citation set |
| Local schema | `LocalBusiness` (or appropriate subtype) on every location page, validated in Rich Results Test |
| Review profile | Response rate >80%, average rating >=4.2, monthly review volume >=competitor median |
| Map Pack visibility | Top 3 for branded + priority commercial queries within a 5km radius of each location |
| CWV on location templates | LCP <2.5s, INP <200ms, CLS <0.1 across mobile |

## Outputs

- `clients/<client-slug>/audits/local/local-audit-v1.md` — full prioritized audit deck.
- `clients/<client-slug>/audits/local/gbp-<location>.md` — one per location.
- A prioritized fix list ready to convert into ongoing retainer scope.
- Map Pack visibility baseline added to the monthly white-label reporting pack.

## Anti-patterns

- Treating local SEO as a citation-only exercise. NAP cleanup is table stakes; it is not the audit.
- Recommending review-velocity hacks (incentivized reviews, fake review pushes) that violate Google's review policy.
- Spinning location pages from a template with thin variation — same helpful-content risk as bad programmatic SEO at scale.
- Ignoring Core Web Vitals on location templates because they "feel local". Mobile users on cellular hate slow location pages.
- Auditing without the local competitor set — context is what separates a finding from a complaint.
- Skipping a per-location section on multi-location clients because the global story "is the same".

## Reference

Pair this skill with:

- `technical-seo-audit` for the site-wide crawl/render/CWV layer.
- `schema-markup-implementation` for `LocalBusiness` and related types.
- `programmatic-seo-at-scale` when location-page templates need a governance pass.
