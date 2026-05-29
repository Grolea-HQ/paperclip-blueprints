---
schema: agentcompanies/v1
slug: authority-site-audit
name: authority-site-audit
description: 'Run a full quarterly audit on a portfolio site — content, technical, link profile, monetization, economics — and produce a kill / hold / scale verdict.'
---

# authority-site-audit

*How Niche Site Empire audits a portfolio site quarterly and produces a single, written kill-or-scale verdict — because 80/20 site economics only work if we actually kill the losers.*

## When to load this skill

- Quarterly portfolio review is scheduled (every site, every quarter, no exceptions).
- A site approaches the 9-month mark and is under $200/month — kill-list candidate.
- A site has just crossed $1K/month for the first time and we are deciding whether to push it onto the scale rail.
- A core update lands and we need to re-assess kill / hold / scale verdicts portfolio-wide.
- The Portfolio Owner is preparing a Flippa or Empire Flippers listing and needs an audit-grade revenue and asset summary.

## Inputs

- Google Search Console + GA4 access for the site (last 12 months).
- Ahrefs / Semrush export of the link profile (referring domains, anchor distribution, toxic ratio).
- Affiliate dashboard data (EPC by cluster, commission rates, top-revenue articles).
- Ad-network dashboard data (RPM trend, fill rate — Ezoic, Mediavine, or AdThrive).
- Content investment ledger to date (articles published, refresh count, link campaigns funded).

## Procedure

The audit runs as five sequential modules, then resolves into one verdict. Each module produces a written sub-report; verdict-less audits are wasted effort.

1. **Content audit.** Total articles, average article age, articles ranking top 10, articles slipping out of top 20, zombies (no impressions in 90 days). Flag clusters where content velocity stalled.
2. **Technical audit.** Indexation rate, Core Web Vitals pass rate (CrUX field data, not Lighthouse), schema coverage, broken-link count, sitemap freshness.
3. **Link profile audit.** Referring domains count and trajectory, DR trajectory, toxic-link ratio (Ahrefs spam-score weighted), lost links over last 90 days.
4. **Monetization audit.** RPM trend, affiliate EPC by cluster, ad fill rate, sponsored content pipeline. Map revenue back to specific clusters so the kill / scale decision is data-grounded.
5. **Economics audit.** Last-90-day revenue, trailing-12-month revenue, content investment to date (writer + editor + link spend), payback period, projected next-12-month revenue at current trajectory.

Then resolve the verdict using the rubric:

- **Scale** — site is over $1K/month, growing month-over-month, CWV green, indexation healthy. Increase content velocity, fund a digital PR campaign, evaluate ad-network upgrade.
- **Hold** — site is $200-$1K/month, flat. Maintain the refresh calendar; do not invest new content velocity. Re-audit next quarter.
- **Kill** — site is under $200/month after 9 months of investment. Sunset on the next CEO review. Either sell on Flippa / Empire Flippers or 301 the best assets into a sibling site in the portfolio.

## Outputs

- `portfolio/<site-slug>/audit/<YYYY-QQ>-audit.md` — the full audit with all five modules, verdict, and the recommended next-quarter actions.
- `portfolio/kill-list.md` — updated row for the site if the verdict is Kill, including sunset date and disposition (sell / 301 / deindex).
- `portfolio/scale-list.md` — updated row if the verdict is Scale, including investment recommendation for the next quarter.
- A one-page summary in the weekly portfolio report for the CEO.

## Anti-patterns

- Audits that recommend "improvements" without a verdict. We do not have improvement budget for hold-or-kill sites.
- Sentimental holds. A site that has been "almost profitable" for 9 months is a kill — kill ruthlessly + scale winners is the doctrine, not a slogan.
- Audits that ignore link profile because the data is hard to pull. Toxic-link ratio kills sites silently and is the most common cause of unexplained ranking decay.
- Recommending Scale on a site with CWV in the red. Scale on a broken technical foundation is throwing content into a leaky bucket.
- Producing the audit without involving the affiliate-program-manager. Revenue attribution by cluster is the load-bearing input for the verdict.

## Reference

Pair this skill with:
- `penalty-recovery-protocol` when the audit surfaces a 20%+ traffic drop.
- `content-refresh-calendar` when the audit recommends Hold.
- `domain-acquisition-diligence` when the verdict is Kill-and-redeploy-capital.
