---
schema: agentcompanies/v1
slug: affiliate-network-setup
name: affiliate-network-setup
description: 'Onboard a portfolio site to Amazon Associates, ShareASale, Impact, and CJ in the right order — including disclosure rails and EPC tracking.'
---

# affiliate-network-setup

*How Niche Site Empire wires a new portfolio site to affiliate networks without breaking TOS, tanking EPC, or triggering rejections that cost us a 90-day cool-down.*

## When to load this skill

- A new portfolio site has just hit 10 published articles and an About page with a real author bio.
- An existing site needs its affiliate stack expanded (e.g., crossing the 30-article threshold that unlocks Impact merchants).
- An affiliate program closes, drops commission rates, or rolls out new compliance requirements and we need to rewire links across one or more sites.
- Affiliate EPC on a content cluster drops below $0.30 and we are evaluating switching the cluster to a higher-payout merchant.

## Inputs

- Site URL, niche, and current article count (must be 10+ for Amazon, 30+ for Impact).
- About page live with a real, credentialed author bio (see `eeat-author-bio-authoring`).
- Privacy policy and affiliate disclosure page already published.
- Approved product list from the content brief, with merchant preferences and confirmed program availability.
- Site speed and Core Web Vitals report — affiliate-link plugins add JS weight that must fit the CWV budget.

## Procedure

Networks are onboarded in a fixed order to minimise rejection risk and to compound approvals:

1. **Amazon Associates** — apply on the day the site has 10 published articles. Amazon checks site quality on approval and again at the first qualifying sale. Disclosure block must say "As an Amazon Associate I earn from qualifying purchases" on every page with Amazon links. Configure the SiteStripe tag (`?tag=siteid-20`) before any link is placed.
2. **ShareASale** — apply once Amazon is approved. Lower bar than Amazon. Useful for the long tail of merchant programs. Approval is per-merchant, so request the top 5 merchants for the niche in the first week.
3. **Impact** — apply once the site has 30+ articles. Higher-tier direct brand programs live here. Approval is by individual merchant, not network-wide. Build the merchant request queue from the content brief's product list.
4. **CJ Affiliate** — apply last, once the site has established traffic (10K+ monthly sessions). CJ requires traffic for approval on its better merchant programs.

Then, per site, run the compliance checklist:

- Privacy policy + affiliate disclosure page live and linked from the footer.
- Per-article disclosure block visible above the fold on any article with affiliate links.
- All affiliate links carry `rel="sponsored"` per Google guidelines; `rel="nofollow"` is not required.
- Cloaking via short-link plugin (e.g., ThirstyAffiliates) is fine; cloaking that hides the destination merchant domain is NOT.
- EPC tracking wired per content cluster — we switch merchants when rates drop.

## Outputs

- `sites/<site-slug>/affiliate/network-status.md` — a row per network with application date, approval date, merchant IDs, and link tagging convention.
- `sites/<site-slug>/affiliate/disclosure-blocks.md` — the exact disclosure copy for each network, ready to paste into the site template.
- `sites/<site-slug>/affiliate/epc-by-cluster.csv` — refreshed monthly, used to drive merchant-switch decisions.

## Anti-patterns

- Applying to Amazon before there are 10 articles. Rejection requires reapplication and resets the clock.
- Forgetting `rel="sponsored"` on affiliate links — Google guideline violation that silently throttles rankings.
- Cloaking links in a way that hides the merchant domain entirely. TOS violation on most networks.
- Treating affiliate setup as set-and-forget. Networks change commission rates; we track EPC by cluster and switch programs when rates drop.
- Onboarding networks out of order (e.g., chasing CJ before Amazon is approved). The order exists because each approval makes the next easier.
- Letting writers pick affiliate products. Product selection is the affiliate-program-manager's job, locked in the content brief.

## Reference

Pair this skill with:
- `content-brief-templates` for the product-list contract that feeds affiliate links into every article.
- `eeat-author-bio-authoring` for the bio quality bar Amazon and Mediavine both check.
- `ezoic-mediavine-ad-configuration` because affiliate disclosure rules interact with sponsored-content rules.
