---
schema: agentcompanies/v1
slug: site-speed-optimization
name: site-speed-optimization
description: 'Tune Core Web Vitals (LCP, INP, CLS) on portfolio sites to publishing-gate standard — image, font, JS, and ad-stack budgets measured on CrUX field data.'
---

# site-speed-optimization

*How Niche Site Empire keeps Core Web Vitals green across the portfolio — because CWV is a ranking signal, an ad-network qualification requirement, and a publishing gate: if a site drops out of "Good", no new content publishes until it is restored.*

## When to load this skill

- A portfolio site drops out of "Good" on any Core Web Vitals metric (LCP, INP, or CLS) on CrUX field data.
- A new portfolio site is launching and needs its CWV baseline configured before traffic arrives.
- A WordPress plugin is added that touches the front-end JS or CSS bundle.
- An ad-stack change is shipped (new network, new ad slot, vignette toggle).
- Mediavine or AdThrive application is being prepared — they review CWV as part of approval.

## Inputs

- CrUX field-data export for LCP, INP, CLS for the last 28 days (Google PageSpeed Insights API or Search Console Core Web Vitals report).
- Current ad-network configuration from `ezoic-mediavine-ad-configuration`.
- Plugin inventory with JS payload per plugin.
- Image and font audit (page-weight by asset type).
- Cloudflare or CDN configuration for the site.

## Procedure

### Portfolio targets (publishing gate)

- **LCP (Largest Contentful Paint):** under 2.0s on mobile (target), 2.5s ceiling.
- **INP (Interaction to Next Paint):** under 150ms (target), 200ms ceiling.
- **CLS (Cumulative Layout Shift):** under 0.05 (target), 0.1 ceiling.

Measured on CrUX field data, not Lighthouse lab scores. Lighthouse is for debugging; CrUX is the truth.

### Fix priority order

1. **Image weight.** Convert to WebP / AVIF. Lazy-load below the fold. Set explicit width/height to prevent CLS. Hero <100KB, inline <50KB.
2. **Font loading.** `font-display: swap` on every web font. Preload the hero font. Drop unused weights. Self-host where possible.
3. **Ad stack.** Lazy-load below the fold. Reserve slot dimensions. Follow each network's CWV playbook. One ad max above the fold on mobile.
4. **JavaScript.** Defer non-critical JS. Audit plugin bloat — every WordPress plugin pays a CWV tax.
5. **Server response.** TTFB under 600ms. Cloudflare in front of every site. Server-side + page cache configured.

### Weekly cadence

- Monday: pull CrUX report for every Scale and Hold site. Flag any metric in "Needs Improvement" or "Poor".
- Wednesday: ship fixes against flags from Monday's report.
- Friday: re-pull CrUX. Document week-over-week movement.
- Any site that drops to "Poor" on any metric — publishing freezes on that site until restoration.

## Outputs

- `sites/<site-slug>/cwv/baseline.md` — current LCP / INP / CLS with target gap and fix priority.
- `sites/<site-slug>/cwv/weekly-log.csv` — append-only weekly readings, used by the authority-site-audit.
- `sites/<site-slug>/cwv/fix-log.md` — fix-by-fix log: change shipped, hypothesized impact, measured impact 7 days later.
- An updated row in `portfolio/cwv-status.md` showing each site's traffic-light status across the three metrics.

## Anti-patterns

- Chasing Lighthouse scores instead of CrUX field data. Lighthouse is synthetic and frequently disagrees with what Google actually ranks on.
- Adding a "speed plugin" that adds its own JS payload. Speed plugins often net-negative once their own runtime is counted.
- Letting ad slots run without reserved dimensions — guaranteed CLS regression and the most common source of slippage.
- Treating speed as a launch-time concern. CWV degrade slowly as content and plugins accumulate; weekly scans are non-negotiable.
- Publishing new content on a site that has dropped to "Poor". The freeze is the lever — bypass it and the site never recovers.
- Optimising mobile and ignoring desktop. Mobile is the priority, but desktop regressions are still a signal.
- Removing a plugin without testing the replacement workflow. Plugin churn breaks editorial flow.

## Reference

Pair this skill with:
- `ezoic-mediavine-ad-configuration` because the ad-stack is usually the largest CWV regressor.
- `schema-markup-implementation` because schema runs alongside CWV as the second publishing gate.
- `penalty-recovery-protocol` when CWV slippage is implicated in a core-update drop.
