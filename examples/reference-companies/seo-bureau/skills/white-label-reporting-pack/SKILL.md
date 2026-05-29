---
schema: agentcompanies/v1
slug: white-label-reporting-pack
name: white-label-reporting-pack
description: 'Assemble and ship the monthly client report so the same artifact can be branded under SEO Bureau or a partner agency without rework — branded, white-label, or (rare) hybrid mode.'
---

# white-label-reporting-pack

*How the client-reporting-manager and reporting-engineer assemble and deliver the monthly report that lands on the first business day of every cycle, branded or white-label, without mixing the two.*

## When to load this skill

- It is the 25th of the month and the monthly report production cycle has started.
- A new partner agency has onboarded the white-label tier and the first report is due in their brand.
- The engagement letter switches a client between branded and white-label mode mid-engagement.
- A recovery retainer is active and the stripped-down weekly recovery report needs to flow into the standard monthly pack.
- The Head of Accounts flags a report at risk of slipping past the first business day deadline.

## Inputs

- Dashboard data assembled per `gsc-ga4-reporting-dashboard` for the reporting period.
- Link-section data from `clients/<client-slug>/links/velocity-tracker.md` with referring-domain delta and anchor distribution.
- Content-section data: briefs shipped, articles published, top performers, top underperformers from the content-strategist's tracker.
- Technical-section data: indexation, Core Web Vitals, schema status, errors fixed from the tech-seo-lead.
- Engagement letter confirming branded vs. white-label vs. hybrid output, plus the correct logo and color tokens.

## Pack components

1. **Cover deck.** Client logo (or partner agency logo), report period, primary KPIs.
2. **Executive summary.** Three-number TL;DR, three-bullet findings, one-bullet next-month focus.
3. **Ranking velocity.** Priority keywords, share of voice, SERP-feature gains/losses.
4. **Traffic and conversions.** Sessions, conversions, revenue (where available), landing-page cluster breakdown.
5. **Technical health.** Indexation, Core Web Vitals (LCP, INP, CLS) per priority template, schema status, errors fixed.
6. **Content section.** Briefs shipped, articles published, top performers, top underperformers, content velocity vs. retainer tier.
7. **Link section.** New referring domains, anchor distribution, DR profile, link-velocity trend vs. 20% MoM ceiling.
8. **Findings + next-month bullets.** Plain English, written by client-reporting-manager.

## Production cadence

| Day | Owner | Action |
|-----|-------|--------|
| 25th | reporting-engineer | Pull data; validate completeness; flag gaps same-day |
| 26th–27th | reporting-engineer | Drop numbers into the report template per client |
| 28th–last business day | client-reporting-manager | Write findings + next-month bullets, apply brand, QA-review |
| First business day of new month | account-manager | Deliver to client (branded) or partner agency (white-label) |
| Same day, if late | CEO + account-manager | Escalation; the client never learns the report is late from anyone else |

## Branding rules

- **Branded mode.** SEO Bureau logo, colors, contact details. Used when the client engaged us directly.
- **White-label mode.** Partner agency logo, colors, contact details. SEO Bureau is invisible — no footer mention, no template watermark.
- **Hybrid mode.** Rare. Only when the engagement letter explicitly approves; CEO sign-off required.

## Outputs

- `clients/<client-slug>/reporting/report-<yyyy-mm>.md` — the source-of-truth monthly report.
- `clients/<client-slug>/reporting/report-<yyyy-mm>.pdf` — the delivered artifact (branded or white-label).
- An entry in the internal retainer-health view used by the CEO and Head of Accounts for weekly retainer math.
- A "next-month focus" carried forward into the following month's retainer plan.

## Anti-patterns

- Mixing branded and white-label assets in a single report. The brand mode is one or the other.
- Shipping numbers without narrative. The narrative is the reason the client reads the report.
- Letting the report slip past the first business day without same-day CEO escalation through the account-manager.
- Pulling data on the 1st of the month instead of the 25th — the late pull is what causes late delivery.
- Sharing internal retainer-math language with the client. The client gets findings and next-month focus, not MRR math.
- Recycling last month's findings because the numbers look similar. The narrative is rewritten every cycle.

## Reference

Pair this skill with:

- `gsc-ga4-reporting-dashboard` for the data layer feeding every section.
- `backlink-acquisition-playbook` for the link section.
- `technical-seo-audit` for the technical-health section.
- `client-onboarding-sequence` when a new client's first report is due.
