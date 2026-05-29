---
schema: agentcompanies/v1
slug: seo-sales-audit-authoring
name: seo-sales-audit-authoring
description: 'Author the short pre-sale SEO audit that converts a qualified lead into a signed productized retainer — without giving away the full audit-tier deliverable for free.'
---

# seo-sales-audit-authoring

*How the bd-sales-lead and seo-analyst produce the 60–90 minute sales audit that proves the bench without cannibalizing the paid audit tier.*

## When to load this skill

- A qualified inbound lead reaches the proposal stage with budget, retainer-math fit ($2.5K/month floor), and a real decision-maker confirmed.
- An outbound prospect asks "what would you do for us" before a discovery call is on the calendar.
- A partner agency requests a white-label sales audit for their own prospect.
- An expired prospect re-engages and the previous sales audit is more than 6 months old.

## Inputs

- Qualified prospect record with company, vertical, site URL, decision-maker, and stated organic-traffic goal.
- Public-data access to the prospect's site, SERP visibility, and link profile (no client GSC at this stage).
- Surface-level crawl of the top 100 URLs from Screaming Frog or Sitebulb — no logs, no full render, no schema deep-dive.
- One hour of senior IC time from the seo-analyst. The sales audit is capped at 60–90 minutes by design.
- Approved productized service tiers price sheet so each finding maps to a deliverable.

## Boundaries

The sales audit surfaces 3–5 high-leverage findings — enough to prove the bench and the productized tier scope, not enough to substitute for the paid audit-tier deliverable. More than 5 findings is a sales mistake.

## Procedure

1. **Quick crawl.** Top 100 URLs. Capture status codes, redirect chains, canonical conflicts, Core Web Vitals snapshot, indexation patterns.
2. **GSC + GA4 public-data review.** Public visibility tools only. Identify indexation gaps, ranking declines, SERP-feature opportunities the prospect misses.
3. **Top 3–5 findings.** Each one a named issue with an estimated organic-traffic impact and a one-line fix. No generic "improve site speed" — name the template, the metric, the fix.
4. **Tie each finding to a productized tier.** Each maps to an audit-tier or ongoing-retainer deliverable; the proposal makes the bridge explicit.
5. **Loom or live walkthrough.** 10-minute Loom or 20-minute live walkthrough. Plain prose decks under-convert.
6. **Proposal pairing.** Bd-sales-lead pairs the audit with a productized proposal — audit tier ($4K–$8K), ongoing retainer ($2.5K–$8K/month), or recovery retainer ($6K–$12K/month, three-month minimum).
7. **CEO review for high-value proposals.** Any proposal over $8K/month or any recovery retainer requires CEO sign-off before send.

## Finding template

- **What** — the named issue (template / cluster / signal).
- **Evidence** — the public-data screenshot or crawl row.
- **Why it matters** — estimated traffic impact range, with the assumption named.
- **One-line fix** — the next step, owned by which productized tier.

## What stays out

- Full prioritized fix list — that is the audit tier.
- Content cluster plan — that is the audit tier.
- Link approved-source list — that is the retainer.
- Recovery diagnosis — that is the recovery retainer kickoff.
- Anything past 90 minutes of senior IC time.

## Outputs

- `prospects/<prospect-slug>/sales-audit-v1.md` — the written audit, capped at 3–5 findings.
- `prospects/<prospect-slug>/sales-audit-loom.txt` — the Loom or walkthrough recording URL.
- `prospects/<prospect-slug>/proposal-v1.md` — the productized proposal that maps findings to a signed retainer tier.
- A CRM stage update reflecting the audit shipped and the proposal sent.

## Anti-patterns

- Shipping a 40-page sales audit and giving away the engagement. Three to five findings, no more.
- Findings without estimated traffic impact. Numbers are what move a proposal.
- Findings the prospect's in-house team already knows about.
- Sales audits without a proposal stapled to them. The audit exists to convert.
- Spending more than 90 minutes — retainer math does not survive 4-hour sales audits.
- Confusing the sales audit with the audit tier. Different scopes, different prices.

## Reference

Pair this skill with:

- `technical-seo-audit` for the paid audit-tier deliverable the sales audit points toward.
- `client-onboarding-sequence` for the post-signature handoff.
- `algorithm-recovery-protocol` when the prospect arrived because of a traffic drop.
