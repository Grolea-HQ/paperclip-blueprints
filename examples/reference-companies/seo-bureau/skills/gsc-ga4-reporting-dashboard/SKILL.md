---
schema: agentcompanies/v1
slug: gsc-ga4-reporting-dashboard
name: gsc-ga4-reporting-dashboard
description: 'Build and maintain the GSC + GA4 dashboard that powers every white-label monthly client report and the internal retainer-health view — ranking velocity, traffic, conversions, and link delta in one place.'
---

# gsc-ga4-reporting-dashboard

*How the reporting-engineer and client-reporting-manager assemble the dashboard that drives every white-label monthly report and the CEO's weekly retainer-math review.*

## When to load this skill

- A new client onboarding has crossed Day 3 and the baseline dashboard must exist before Day 10.
- The monthly report production cycle hits the 25th of the month and the data pull starts.
- A quarterly retainer review is on the calendar with the Head of Accounts.
- A recovery sprint demands a weekly stripped-down view of ranking velocity and indexation delta.
- The CEO requests the weekly retainer-health snapshot for the Monday review.

## Inputs

- Verified Google Search Console (full) and GA4 (read) access from onboarding.
- Priority keyword set agreed with the client during onboarding.
- Internal link-velocity tracker from `clients/<client-slug>/links/velocity-tracker.md`.
- Rank-tracker share-of-voice export for the client's competitive set.
- Engagement letter confirming branded vs. white-label vs. (rare) hybrid output mode.

## Data sources

- **Google Search Console** — impressions, clicks, CTR, average position, queries, pages, Core Web Vitals (CrUX field data), Rich Results coverage.
- **Google Analytics 4** — sessions, conversions, revenue, channel attribution, landing-page reports.
- **Internal link-velocity tracker** — referring-domain delta, anchor distribution, DR profile.
- **Rank tracker** — priority keyword set, share of voice, SERP-feature wins/losses.
- **Internal retainer-math sheet** — MRR, churn risk, retainer tier, contract month.

## Procedure

1. **Baseline (Day 3–10 of onboarding).** Wire GSC + GA4 connections. Define the priority keyword set. Snapshot to `clients/<client-slug>/reporting/baseline-v1.md`.
2. **Monthly pull (25th).** Reporting-engineer pulls data on the 25th — never the 1st. Validate completeness; escalate same-day on GSC gaps or broken GA4 attribution.
3. **Generate the dashboard view** following the section structure below.
4. **Narrative pass.** Client-reporting-manager writes findings + next-month bullets in plain English. Reporting-engineer owns numbers; manager owns prose.
5. **Brand application.** Branded (SEO Bureau) when the client engaged us directly. White-label (partner agency) when a partner resells our retainer. Never mix.
6. **Deliver on the first business day.** Late reports trigger same-day CEO escalation through the account-manager.

## Dashboard sections

1. **Executive summary.** Three numbers: organic sessions MoM, conversions MoM, MRR-attributable organic revenue MoM.
2. **Ranking velocity.** Movement in priority keywords, share of voice, SERP feature wins/losses.
3. **Traffic and engagement.** Sessions by landing-page cluster, top gainers, top losers, indexation health.
4. **Conversions.** Goal completions or revenue from organic, attributed by landing-page cluster.
5. **Core Web Vitals.** LCP, INP, CLS per template; regressions tagged with code or asset cause.
6. **Link profile.** New referring domains, anchor distribution, DR profile, link-velocity trend versus the 20% MoM ceiling.
7. **Findings.** 3–5 bullets summarizing what changed and why, plain English.
8. **Next month's focus.** What the retainer will ship next cycle.

## Outputs

- `clients/<client-slug>/reporting/dashboard-<yyyy-mm>.md` — monthly dashboard snapshot.
- The dashboard view itself, branded or white-label, delivered to the client on the first business day.
- An entry in the internal retainer-health view used by the CEO and Head of Accounts.

## Anti-patterns

- Dashboards that are 30 charts deep with no narrative. Numbers without prose are noise.
- Reports that show movement without explaining cause.
- Pulling data on the 1st of the month and shipping late. The 25th is the pull date.
- Mixing branded and white-label assets in a single report. The brand mode is one or the other.
- Letting the link section live somewhere other than the dashboard — the link-velocity tracker is a primary section, not an appendix.
- Treating Core Web Vitals as a one-line "all green" check instead of a per-template diagnosis.

## Reference

Pair this skill with:

- `white-label-reporting-pack` for the deck-level assembly and delivery cadence.
- `technical-seo-audit` for the Core Web Vitals diagnosis feeding the dashboard.
- `backlink-acquisition-playbook` for the link section.
