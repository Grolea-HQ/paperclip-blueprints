---
schema: agentcompanies/v1
slug: keyword-cluster-research
name: keyword-cluster-research
description: 'Find, score, and approve low-competition, high-intent keyword clusters that justify a content investment on a portfolio site — never a single keyword.'
---

# keyword-cluster-research

*How Niche Site Empire finds keyword clusters worth a content investment across the portfolio — because we invest in clusters, not single keywords, and the rubric is what protects 80/20 site economics.*

## When to load this skill

- A portfolio site needs its next content cluster identified for the editorial calendar.
- A new domain has been acquired and seed clusters need scoring before any briefs are written.
- A competitor gap analysis has surfaced a candidate cluster and we need to score it.
- An affiliate program rate increase makes a previously borderline cluster viable.

## Inputs

- Target portfolio site (given niche fit and cannibalisation rules).
- Ahrefs / Semrush keyword export with monthly volumes and KD/DA.
- Top-10 SERP analysis for the hero keyword (who ranks, content type, age, link profile).
- Affiliate program data: average product price × commission rate × conversion benchmark.
- Existing portfolio coverage map — which sites already cover which niches.

## Procedure

Every candidate cluster is scored on five axes before any brief is written. A cluster that fails any single axis is rejected.

1. **Volume floor.** Cluster total monthly search volume must be at least 3,000 across the hero plus supporting keywords. Below that, the math does not work even with great rankings.
2. **Competition ceiling.** Average KD (Ahrefs) or DA of top-10 results must be under 40 for the hero terms. If we are competing with Wirecutter, NYT Wirecutter, or other tier-1 publications, walk away — link budget will not close the gap.
3. **Intent.** Commercial or transactional intent for affiliate clusters; informational for display-ad clusters. Mixed-intent clusters get split into two clusters that ladder into separate hub posts.
4. **Affiliate EPC potential.** For commercial clusters, compute average product price × commission rate × conversion benchmark. Below $0.30 EPC, the cluster is not worth the writing budget regardless of volume.
5. **Cannibalisation check.** Does another site in the portfolio already cover this cluster? If yes, do not duplicate — extend the existing site instead, or reject the cluster.

Once a cluster passes all five axes, produce the cluster brief:

- Cluster name (e.g., "electric pruners for arthritis").
- Hero keyword + 8-40 supporting keywords with volumes and KD.
- Intent classification (commercial / informational / mixed-then-split).
- Target site.
- Expected EPC and projected RPM if display-ad-monetized.
- Top-10 SERP analysis: who ranks, content type, gaps.
- Internal linking plan: hero-to-supporting and supporting-to-supporting.

Content-director signs off before any article brief is generated downstream.

## Outputs

- `sites/<site-slug>/clusters/<cluster-slug>/cluster-brief.md` — the full scored brief with rubric scores and SERP analysis.
- `sites/<site-slug>/clusters/<cluster-slug>/keywords.csv` — hero + supporting keywords with volumes, KD, intent, and target URL slugs.
- `portfolio/cluster-map.md` — updated row mapping the cluster to its target site, to enforce the cannibalisation rule.
- `sites/<site-slug>/clusters/<cluster-slug>/internal-link-plan.md` — the hub-and-spoke link plan, used by every downstream brief.

## Anti-patterns

- Picking a cluster because it "looks easy" without running the EPC math. Easy clusters with no buyer signal are display-ad-only at best.
- Skipping the cannibalisation check and overlapping two portfolio sites on the same cluster.
- Confusing high volume with high intent. Informational queries with no buyer signal do not pay.
- Letting writers pick keywords. Writers ship briefs; the brief is built from this rubric upstream.
- Scoring a single hero keyword instead of the full cluster. A 25-article cluster compounds; a single article does not.
- Approving a cluster that fails one axis but "feels right". Sentiment is not a sixth axis.

## Reference

Pair this skill with:
- `content-brief-templates` for the downstream article briefs the cluster feeds.
- `programmatic-page-generation` when a cluster's long-tail tail is dense enough to template.
- `authority-site-audit` because cluster-level revenue mapping is the load-bearing input for kill / scale verdicts.
