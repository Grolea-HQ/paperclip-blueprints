---
schema: agentcompanies/v1
slug: technical-seo-audit
name: technical-seo-audit
description: 'Run the end-to-end SEO Bureau technical audit — crawl, render, indexation, Core Web Vitals, schema, log-file analysis — and produce a prioritized fix list that converts into ongoing retainer scope.'
---

# technical-seo-audit

*How the tech-seo-lead and crawl-render-specialist ship the audit-tier deliverable that anchors the audit-to-retainer conversion path.*

## When to load this skill

- A new audit-tier engagement ($4K–$8K) has been signed and the kickoff is complete.
- A new ongoing-retainer client crosses Day 10 of onboarding and the baseline audit must ship by Day 21.
- A recovery retainer kicks off after an algorithm update and the technical layer must be re-audited.
- A retainer client requests a re-audit at the 6-month or 12-month renewal point.
- The monthly white-label reporting pack flags a technical regression that needs deeper diagnosis than the dashboard allows.

## Inputs

- Verified GSC (full) and GA4 (read) access.
- Crawl tooling provisioned: Screaming Frog, Sitebulb, or equivalent.
- Server log access for crawl-budget analysis (request via account-manager if missing; mark the section deferred if it never arrives).
- Confirmed retainer tier and audit scope (template SMB vs. enterprise mid-market).
- Cluster plan and link-velocity tracker when the audit is part of onboarding.

## Procedure

1. **Crawl baseline.** Full crawl with JS rendering enabled. Capture status codes, redirect chains, canonical conflicts, hreflang errors, orphan pages, depth distribution. Output to `clients/<client-slug>/audits/crawl-<yyyy-mm-dd>.csv`.
2. **Render audit.** Compare crawl render vs. raw HTML on the top 50 templates. Flag client-side-only content as a render risk with template, missing content, and recommended fix.
3. **Indexation review.** Pull GSC Coverage. Categorize URLs as indexed, excluded (with reason), or error. Flag faceted-nav explosions, soft-404 clusters, canonical mis-targeting.
4. **Core Web Vitals.** Pull CrUX field data plus lab data per template. Diagnose LCP, INP, CLS regressions. Tie each to a code or asset cause — hero image, third-party script, embedded map, shifting ad slot.
5. **Schema audit.** Validate existing structured data with Rich Results Test and Schema.org validator. Identify missing high-leverage types (`Product`, `Article`, `FAQPage` where genuine, `HowTo`, `Organization`, `BreadcrumbList`).
6. **Log-file analysis.** Bot hits per template, crawl-budget waste, soft-404 patterns, status-code distribution. If logs are unavailable, mark deferred.
7. **Prioritize.** Rank findings by traffic impact x effort. Output the top 20 fixes with named templates and owners.
8. **Deck.** Ship the audit on the white-label audit template. Executive summary, prioritized fixes, implementation plan, 90-day projected impact range with the "Google does not guarantee timelines" disclaimer in recovery contexts.

## Severity matrix

| Severity | Definition | SLA from sign-off |
|----------|------------|-------------------|
| P0 | Manual action, indexation collapse, site-wide CWV failure | Immediate — recovery sprint kicks in |
| P1 | Template-level regression, schema errors, render gaps | Inside 30 days of retainer cycle |
| P2 | Crawl-budget waste, minor canonical drift | Next 60 days |
| P3 | Optimization opportunities, nice-to-have schema additions | Backlog, reviewed at quarterly retainer review |

## Outputs

- `clients/<client-slug>/audits/technical-v1.md` — client-ready audit deck.
- `clients/<client-slug>/audits/crawl-<yyyy-mm-dd>.csv` — raw crawl export.
- `clients/<client-slug>/audits/fix-list-v1.md` — prioritized fix list with severity, owner, and projected impact, ready to convert into monthly retainer scope.
- A retainer-scope mapping note that bridges findings to next month's productized service tier deliverables.

## Anti-patterns

- Generic "200 issues" reports. The deck ships with the top 20, not the top 200.
- Findings without prioritization or projected impact.
- Recommendations that require unscoped dev work. Each fix names an owner.
- Shipping without the Core Web Vitals diagnosis because "the dashboard is green". CrUX field data hides template-level pain.
- Skipping the log-file section without flagging it as deferred. Silent omissions cost trust.
- Treating the audit as a one-off — it feeds the GSC + GA4 dashboard baseline and the link-velocity tracker.

## Reference

Pair this skill with:

- `client-onboarding-sequence` for the Day-10-to-Day-21 audit slot.
- `schema-markup-implementation` for the schema deep-dive when the audit calls for it.
- `algorithm-recovery-protocol` when the audit is part of a recovery sprint.
- `gsc-ga4-reporting-dashboard` for the post-audit monitoring layer.
