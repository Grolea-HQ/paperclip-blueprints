---
schema: agentcompanies/v1
slug: penalty-recovery-protocol
name: penalty-recovery-protocol
description: 'Diagnose and recover from Google manual actions and core-update drops — content quality, link profile, technical — as a CEO-approved campaign, not an autonomous fix.'
---

# penalty-recovery-protocol

*How Niche Site Empire responds when a portfolio site drops 20%+ after a core update or receives a manual action — because penalty recovery is a CEO-approved campaign, not an autonomous panic.*

## When to load this skill

- A portfolio site drops 20%+ in trailing-7-day traffic after a Google core update.
- A manual action notification arrives in Google Search Console.
- A Helpful Content Update flags a site for content-quality risk.
- A site is on Kill watch but the Portfolio Owner wants one rebuild attempt before sunset.

## Inputs

- Pre-drop baseline traffic (trailing 30 days before the event).
- GSC Manual Actions and Security Issues reports.
- Algorithm-update calendar (Search Engine Roundtable / Google's confirmed-update list).
- Full backlink profile export (Ahrefs / Majestic).
- Article inventory with zombie status, impression counts, and refresh history.
- CEO sign-off ticket — recovery work does not start without it.

## Procedure

### Phase 1: Diagnosis triage (within 48 hours)

1. **Identify the trigger.** Manual action notice? Confirmed core update? Algorithm refresh? Indexation issue? Server outage?
2. **Pull the impact report.** Which clusters and pages dropped? Position-drop pattern — uniform sitewide, or concentrated on commercial / affiliate-heavy posts?
3. **Classify the cause.** Content quality, link profile, technical, or unclear. Multiple causes are common — classify the dominant one.

### Phase 2: Recovery by cause

**Content quality (Helpful Content Update / core update):**
- Audit zombie content (no impressions in 90 days). Either rewrite or noindex.
- Audit thin programmatic pages. If dataset variance was insufficient, deindex the set.
- Audit affiliate-thin articles (80% product table, 20% filler) — rewrite with real testing notes, comparisons, original photos.
- Audit author bylines. Anonymous or low-credibility authors — replace with named, credentialed authors.

**Link profile (link spam update or manual action):**
- Pull the full backlink profile. Identify spammy referring domains (Russian PBNs, casino spam, AI-generated comment spam).
- Disavow the worst as a scalpel cut. Do not panic-disavow the whole profile.
- Document the disavow file submission with date, count, and rationale.

**Technical:**
- Crawl errors, indexation drops, schema errors — fix them in priority order.
- Restore Core Web Vitals to green if they have slipped (see `site-speed-optimization`).

### Phase 3: The waiting game

- Manual action: file a reconsideration request with a written summary of fixes and the disavow file path. Expect 1-6 weeks.
- Core update: wait for the next core update (typically 2-4 months). No faster path.
- Recovery may take 1-3 core updates. Plan for the long version.

## Outputs

- `sites/<site-slug>/recovery/<YYYY-MM-DD>/diagnosis.md` — the 48-hour triage document with trigger, impact, and classification.
- `sites/<site-slug>/recovery/<YYYY-MM-DD>/recovery-plan.md` — the recovery playbook with named owners and due dates.
- `sites/<site-slug>/recovery/<YYYY-MM-DD>/disavow.txt` — the disavow file submitted to Google, dated and signed.
- `sites/<site-slug>/recovery/<YYYY-MM-DD>/reconsideration-request.md` — the manual-action reconsideration draft.
- A weekly status entry in the portfolio report until recovery resolves or the site is sunset.

## Anti-patterns

- Panic-disavowing the whole link profile. Disavow is a scalpel, not a hammer — losing healthy links makes recovery harder.
- Mass-deleting articles. Better to noindex and rewrite than delete; deletion removes the URL's history.
- Filing reconsideration requests without actually fixing the underlying issue. Burns goodwill with the team that reviews them and extends recovery cycles.
- Treating recovery as a content-velocity sprint. Recovery is about quality and trust signals, not volume — kill ruthlessly + scale winners still applies.
- Promising the Portfolio Owner a recovery timeline. Recovery may take 1-3 core updates.
- Starting work without CEO sign-off. Recovery campaigns reallocate budget away from the Scale list.

## Reference

Pair this skill with:
- `authority-site-audit` because the audit modules feed the diagnosis triage.
- `eeat-author-bio-authoring` when weak author signals are the dominant cause.
- `site-speed-optimization` when technical CWV slippage is the dominant cause.
