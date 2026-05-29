---
schema: agentcompanies/v1
slug: domain-acquisition-diligence
name: domain-acquisition-diligence
description: 'Diligence a domain (aged or new) before the Portfolio Owner approves the buy — Wayback history, link profile, manual actions, niche fit.'
---

# domain-acquisition-diligence

*How Niche Site Empire diligences a domain before purchase — because a $5K aged domain with a hidden manual action is a $5K loss plus six months of wasted content investment.*

## When to load this skill

- An aged-domain marketplace listing (GoDaddy Auctions, ODYS, Spamzilla) matches a portfolio niche and is under the budget ceiling.
- A broker pitches a private off-market domain to the Portfolio Owner.
- An expired domain crawler surfaces a candidate in a niche where we have content velocity ready to deploy.
- A new (hand-registered) domain is being proposed for a greenfield site and we need to confirm name fit and TLD before launch.

## Inputs

- Target domain name and current asking price.
- Niche or cluster the domain would serve (must map to an existing or planned portfolio site).
- Ahrefs / Majestic API access for link-profile pull.
- Wayback Machine and Whois history access.
- Google Search Console availability for the domain (required before any buy completes).

## Procedure

Run every section of the diligence checklist. Skipping a section is grounds for the Portfolio Owner to reject the buy on principle, even if the rest of the diligence is clean.

1. **Wayback Machine history.** What did the domain run as previously? Adult, gambling, pharma, or PBN-network use is an immediate walk-away. Archive.org snapshots show peak content quality — if it was always thin, the link profile is probably thin too.
2. **Whois history.** Has the domain churned through multiple owners in short succession? Frequent ownership changes are a contamination red flag.
3. **Link profile — referring domains.** At least 30 referring domains from real publications. Below that, the domain is not worth aged-domain pricing.
4. **Link profile — toxic ratio.** Pull the full link profile. If more than 30% of referring links are obviously spammy (Russian PBNs, casino links, AI-generated comment spam, scraper sites), the domain is contaminated and recovery cost exceeds rebuild cost.
5. **Link profile — anchor text distribution.** Healthy distribution of branded, naked URL, and varied keyword anchors. If 80%+ of anchors are exact-match commercial keywords, the domain was used for money-keyword spam.
6. **Manual actions / penalties.** Claim Google Search Console for the domain before the buy completes. Check for active manual actions in the Security & Manual Actions report.
7. **Indexation check.** Run `site:domain.com` in Google. Zero or strange indexed pages may indicate deindexing.
8. **Niche fit.** The domain name must read naturally for the target niche. "BestPruners.com" for a gardening site is fine; "Crypto-Investments-2019.net" for anything is not.
9. **TLD.** .com strongly preferred. .net / .org acceptable. Country TLDs only when the site is country-targeted.
10. **Write the report.** Five-section diligence document with a recommendation: BUY, BUY-AT-LOWER-PRICE, or WALK-AWAY.

## Outputs

- `portfolio/acquisitions/<domain>/diligence-report.md` — the written report covering all 10 checks with screenshots and link exports.
- `portfolio/acquisitions/<domain>/link-profile.csv` — the Ahrefs export the report references.
- `portfolio/acquisitions/<domain>/decision.md` — Portfolio Owner's BUY / WALK-AWAY decision, signed and dated.

## Anti-patterns

- Buying based on DR alone. DR is gameable; toxic-link ratio is not.
- Skipping the Wayback Machine check. Adult-site or pharma histories tank rankings even after years of clean use.
- Buying domains with active manual actions. Recovery is rarely worth the cost versus a clean rebuild.
- Trusting the seller's link export. Always pull our own Ahrefs export — sellers filter toxic links before sending.
- Letting price anchor the decision. A $500 "deal" with a poisoned profile is still a loss.
- Buying without a content velocity plan ready to deploy. Aged domains lose authority fast when crawl returns thin pages.

## Reference

Pair this skill with:
- `penalty-recovery-protocol` when the diligence surfaces recoverable issues we are willing to absorb at a lower price.
- `keyword-cluster-research` to confirm the niche-fit claim with real cluster data.
- `authority-site-audit` for the post-acquisition baseline audit, run within 30 days of onboarding.
