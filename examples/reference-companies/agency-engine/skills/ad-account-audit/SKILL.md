---
schema: agentcompanies/v1
slug: ad-account-audit
name: ad-account-audit
description: 'Run a 14-day channel audit (paid, SEO, lifecycle, social) at retainer onboarding so the first monthly plan stands on a real baseline.'
---

# ad-account-audit

*How Agency Engine baselines a new client's channel before the first Plan week — the audit that anchors every results-vs-plan number we will ever report.*

## When to load this skill

- A new retainer has been signed and the channel lead is inside the 14-day onboarding window.
- A quarterly refresh window is open inside QBR prep and the channel baseline must be re-set.
- An account has turned red on `account-health-scoring` and the channel lead suspects baseline drift.
- A retainer is upgrading tier (Foundation → Growth, Growth → Scale) and a new channel is being added to scope.
- The client mid-retainer migrates platforms (Shopify → BigCommerce, Klaviyo → Mailchimp, GA4 reset) and the baseline needs re-establishing.

## Inputs

- Read access (and where needed, write access) to the client's channel account, granted on Day 1 of onboarding.
- The signed SOW from `scope-of-work-builder` — defines what is in scope and what is not.
- Last 90 days of analytics from the Analyst's baseline pull.
- The brand voice document from `brand-voice-capture` (anchors creative-led findings).
- The discovery brief from the Strategist so findings ladder up to stated client objectives.

## Procedure

1. **Confirm access and scope.** Lock down read access. Confirm the channel is in the signed SOW; if not, stop and route to `scope-creep-recovery`.
2. **Account hygiene scan.** Naming conventions, structure, tracking pixels, attribution wiring, account-level settings.
3. **Performance baseline.** Pull last-90-day metrics anchored to the channel's primary KPI: paid uses ROAS or CAC; SEO uses organic sessions-to-revenue; lifecycle uses revenue-per-recipient; social uses saved/shared engagement and assisted conversions.
4. **Channel-specific efficiency check.** Paid: wasted spend by campaign and audience overlap. SEO: index coverage, crawl errors, content-to-keyword fit. Lifecycle: deliverability, list health, flow coverage gaps. Social: audience drift, posting cadence vs. engagement.
5. **Anti-pattern findings.** What is broken, what is wasteful, what is risky — each with evidence cited (screenshot, query, metric pull).
6. **First-cycle priorities.** The 3-5 things the first monthly plan should tackle, ranked by impact-per-effort.
7. **Open client-side asks.** Tracking gaps, access requirements, engineering dependencies, content needs.
8. **Sign-off and file.** Channel lead signs; Strategist reviews; output filed before Plan week starts.

### Channel-specific deliverable checklist

- **Paid Media Lead:** spend efficiency table, audience overlap report, creative fatigue scan, attribution sanity check.
- **SEO Lead:** crawl report, index coverage, keyword-to-page map, content gap list.
- **Lifecycle Lead:** deliverability score, flow inventory, segment health, revenue-per-recipient by flow.
- **Social Lead:** audience drift report, posting cadence vs. engagement curve, organic-vs-paid mix.

## Outputs

- `clients/<client-slug>/audits/<channel>-<YYYY-MM>.md` containing the seven audit sections, evidence citations, and channel-lead sign-off.
- A 3-5 priority list that feeds directly into `monthly-strategy-review` for Plan week.
- Baseline metrics filed at `clients/<client-slug>/baselines/<channel>-<YYYY-MM>.md` for results-vs-plan comparisons in every future Client Reporting Pack.
- An open client-asks block forwarded to the Account Manager for kickoff call follow-up.

## Anti-patterns

- Findings without source citations — every claim must point to a screenshot, query, or metric pull.
- Audits that recommend out-of-scope work without flagging it as out-of-scope and routing to a change order.
- Cosmetic findings padding (typos in ad copy) instead of decision-driving findings (ROAS-killing audience overlap).
- Skipping the channel-specific efficiency check to "move fast" — the first month's plan will land on sand.
- Auditing a channel the SOW excludes (that is scope creep on our side).
- Shipping audit findings before the brand voice document is captured (creative findings then drift).

## Reference

Pair this skill with:
- `monthly-strategy-review` for translating audit priorities into the first monthly plan.
- `scope-of-work-builder` for verifying channel inclusion before auditing.
- `client-reporting-pack` so the baseline supports every results-vs-plan number going forward.
