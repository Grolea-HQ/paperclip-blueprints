---
schema: agentcompanies/v1
slug: content-refresh-calendar
name: content-refresh-calendar
description: 'Schedule and execute refreshes of declining or stale articles across the portfolio — what to refresh, when, and what ''refreshed'' actually means.'
---

# content-refresh-calendar

*How Niche Site Empire keeps older content ranking without burning content velocity on new drafts — because refreshes compound when new articles only ladder.*

## When to load this skill

- The seo-analyst's Monday position-drift report surfaces articles that dropped 5+ positions over the last 30 days.
- A new calendar year begins and year-tagged titles ("Best X for 2025") need rolling forward across the portfolio.
- A broken-link scan flags affiliate-link rot — merchant programs closing or product SKUs disappearing.
- A core update lands and we are deciding which articles to refresh first as part of the recovery campaign.
- A site is on Hold status from its quarterly audit — refreshes are the only content investment we make on Hold sites.

## Inputs

- GSC + GA4 export of articles ranking positions 4-20 with 30-day position trend.
- Broken-link and merchant-status report from the affiliate-program-manager.
- Article inventory with `last-refreshed` dates and zombie status (no impressions in 90 days).
- Editor capacity for the week — maximum 10 refresh slots per week across the portfolio.

## Procedure

The refresh queue is rebuilt every Monday and worked through across the week.

1. **Build the queue.** Pull candidates from four sources:
    - **Position drift.** Articles that dropped 5+ positions over the last 30 days.
    - **Stale claims.** Articles with year-tagged titles or specific year references.
    - **Affiliate-link rot.** Articles where any tracked affiliate link returns a 404 or where the merchant program closed.
    - **CTR slumps.** Articles ranking top 10 with CTR below the SERP benchmark for that position.
2. **Triage.** Editor reviews the queue Monday 10:00. Reject zombies (they need a rewrite or a kill, not a refresh). Reject articles already refreshed in the last 60 days. Cap the weekly load at 10 refreshes.
3. **Brief.** For each accepted refresh, regenerate the brief using `content-brief-templates`. New SERP context, updated product list, new internal-link targets.
4. **Refresh execution.** A refresh is one of:
    - Updated product list (commercial) with new top picks and verified affiliate links.
    - Updated supporting data (informational) with current statistics, dates, and references.
    - Restructured intro and conclusion to match current SERP intent.
    - Added FAQ section if missing (with FAQPage schema).
    - Republished with updated `lastmod` in sitemap and updated date stamp in the article.
5. **Compliance + publish.** Editor + affiliate-disclosures-compliance review the refresh, same gate as a new article. Publish with the new date stamp and ping the sitemap.
6. **Track.** seo-analyst monitors the article's position for 21 days post-refresh. Refreshes that do not move position trigger a deeper rewrite or a kill.

## Outputs

- `portfolio/refresh-queue.md` — the live queue, rebuilt every Monday, with reason codes and accept/reject status.
- `sites/<site-slug>/articles/<slug>/refresh-log.md` — append-only log of every refresh on the article (date, type, before/after position).
- `portfolio/refresh-impact.csv` — weekly roll-up of refresh count vs. position movement, used to tune the rubric.

## Anti-patterns

- Updating the date stamp without updating the content. Google calls this "false freshness" and discounts it sitewide.
- Refreshing zombies. Zombies need a real rewrite or a kill, not a coat of paint.
- Refreshing during a Google core update. Wait for the dust to settle (typically 2-4 weeks) before judging refresh impact.
- Treating a refresh as a typo fix. A refresh must change something a reader and Google's freshness signals would notice.
- Refreshing past the weekly cap of 10. Burns editor capacity and dilutes the signal we are trying to send Google.
- Skipping the post-refresh tracking. Without it we cannot tell which refresh patterns actually work.

## Reference

Pair this skill with:
- `content-brief-templates` because every refresh needs a regenerated brief.
- `penalty-recovery-protocol` when refreshes are part of a core-update recovery campaign.
- `authority-site-audit` because Hold-verdict sites live entirely on refreshes.
