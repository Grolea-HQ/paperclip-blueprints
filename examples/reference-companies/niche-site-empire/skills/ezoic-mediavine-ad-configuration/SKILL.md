---
schema: agentcompanies/v1
slug: ezoic-mediavine-ad-configuration
name: ezoic-mediavine-ad-configuration
description: 'Configure display-ad networks across the portfolio — Ezoic at launch, Mediavine at 50K sessions, AdThrive at 100K — without tanking Core Web Vitals.'
---

# ezoic-mediavine-ad-configuration

*How Niche Site Empire runs display ads across the portfolio without tanking Core Web Vitals — because RPM and CWV are coupled, and a bad ad stack costs us rankings faster than it earns us revenue.*

## When to load this skill

- A new portfolio site is launching and needs its Ezoic stack configured before first traffic.
- A site has hit 50K monthly sessions for 90 consecutive days and is being evaluated for Mediavine.
- A site has hit 100K monthly pageviews and is being evaluated for AdThrive.
- Core Web Vitals on a production site have slipped and the ad stack is suspect.
- A network rolls out a new ad unit (anchor, vignette, video) and we are deciding portfolio-wide.

## Inputs

- Site's last 90 days of session and pageview data from GA4 / GSC.
- Current ad-network dashboard (RPM trend, fill rate, ad-unit performance).
- CrUX field data for LCP, INP, CLS (not Lighthouse lab scores).
- Site speed report from `site-speed-optimization` with current page-weight budget.
- CEO approval ticket for any network switch.

## Procedure

### The network ladder

| Network | Qualification | Notes |
|---|---|---|
| Ezoic | None (any traffic level) | Default at site launch. Lower RPM than premium networks. |
| Mediavine | 50K monthly sessions, mostly tier-1 traffic | RPM jumps significantly. Strict content quality review on application. |
| AdThrive | 100K monthly pageviews | Highest RPM tier. Premium content and tier-1 traffic required. |

### Per-site configuration rules

- **Lazy-load below the fold.** Mandatory. Without lazy-loading, LCP regresses on mobile.
- **Reserve ad-slot dimensions.** Set explicit width/height on every slot container. Prevents CLS.
- **Limit ads above the fold.** One ad unit above the fold maximum on mobile. Network "auto-insert" defaults often violate this — check and override.
- **Anchor ads with caution.** Persistent bottom anchors hurt UX scores. Test on a sample of pages before enabling sitewide.
- **Vignette / interstitial ads OFF on mobile.** They tank INP and risk Google's intrusive interstitial penalty.
- **Sponsored attribute** on any advertorial unit alongside the network stack.

### Switching networks (Ezoic to Mediavine to AdThrive)

1. seo-analyst confirms the site has hit the qualification threshold for 90 consecutive days, not just a spike.
2. display-ads-manager prepares the application: content review, traffic data, site speed report.
3. CEO approves the switch in writing.
4. Transition: remove old network's code, install new network's code, monitor RPM and CWV for 14 days.
5. Roll back only if RPM drops more than 30% after the 14-day burn-in.

## Outputs

- `sites/<site-slug>/monetization/ad-config.md` — current network, ad-unit map, lazy-load and reservation settings, anchor / vignette toggles.
- `sites/<site-slug>/monetization/rpm-by-month.csv` — trailing-12 RPM trend, used for ladder-upgrade decisions.
- `sites/<site-slug>/monetization/cwv-impact.md` — before/after CrUX field data for every ad-stack change.
- An updated row in `portfolio/network-ladder-status.md` showing each site's current network and next qualification target.

## Anti-patterns

- Applying to Mediavine before the site has 90 days of clean traffic. Rejection has a 90-day cool-down that delays the RPM upgrade by a full quarter.
- Enabling every ad slot the network offers. RPM goes up; CWV crashes; net revenue drops because of ranking loss.
- Forgetting to update sponsorship disclosures when adding direct-sold sponsored content alongside network ads.
- Switching networks based on a single month of strong traffic. Spikes regress.
- Treating Lighthouse lab scores as the CWV authority. CrUX field data is what Google ranks on.
- Pushing AdThrive on a site with thin or programmatic-heavy content. AdThrive rejects on content quality.

## Reference

Pair this skill with:
- `site-speed-optimization` because the ad-stack is usually the largest CWV regressor on a portfolio site.
- `schema-markup-implementation` because sponsored content needs the right attributes alongside schema.
- `authority-site-audit` because the monetization audit module pulls directly from this skill's outputs.
