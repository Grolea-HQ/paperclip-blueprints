---
schema: agentcompanies/v1
slug: algorithm-recovery-protocol
name: algorithm-recovery-protocol
description: 'Diagnose and recover client domains hit by Google core updates, helpful-content updates, link-spam updates, or manual actions — without promising timelines Google does not honor.'
---

# algorithm-recovery-protocol

*How SEO Bureau diagnoses, scopes, and runs a recovery sprint when a client's organic traffic falls off a cliff or GSC posts a manual action.*

## When to load this skill

- A GSC manual action notification lands in a client property the seo-analyst monitors.
- A client property loses 20%+ organic traffic week-over-week and the drop date overlaps a confirmed Google update window.
- The CEO and Head of Accounts have approved a recovery retainer ($6K–$12K/month, three-month minimum) and the recovery sprint must kick off within 72 hours.
- A retainer client's monthly white-label report shows ranking velocity inverting across more than one landing-page cluster.

## Inputs

- Verified GSC + GA4 access, plus the baseline snapshot taken at onboarding (`clients/<client-slug>/reporting/baseline-v1.md`).
- Pre-drop and post-drop crawl from Screaming Frog or Sitebulb, with JS rendering enabled.
- Link profile export from the standard toolset and the active link-velocity tracker.
- Confirmed update window from the Google Search Status Dashboard; if no confirmed update, treat as a separate diagnosis path.
- Signed recovery retainer with the "no guarantee" disclaimer countersigned by the client.

## Procedure

1. **Confirm and snapshot (first 24 hours).** Cross-check the drop date against confirmed update windows. Pull pre/post landing-page cluster data into `clients/<client-slug>/recovery/snapshot-v1.md`. Account-manager and CEO contact the client inside 24 hours — silence is unacceptable.
2. **Classify the diagnosis.** Pick exactly one primary cause:
   - **Core update** → EEAT signals, thin content, topic dilution, author trust, retainer math context.
   - **Helpful content update** → unhelpful or AI-generated patterns, doorway pages, low-value listicles in productized service tiers content.
   - **Link spam update** → spammy anchor patterns, link-velocity discipline failures, paid placements not disclosed.
   - **Manual action** → address verbatim what GSC cites; nothing more, nothing less.
3. **Ship the triage plan (day 7).** Deliver `clients/<client-slug>/recovery/triage-plan-v1.md` to the CEO and client. Plan names the diagnosis, the fix scope, the 90-day projected impact range, and the explicit "Google does not guarantee recovery timelines" disclaimer.
4. **Execute fixes across content quality, technical SEO, and link profile.** Tech-seo-lead owns crawl/render/Core Web Vitals; content-strategist owns content quality and pruning; link-acquisition-lead owns disavow only after a documented diagnosis.
5. **Weekly cadence for 12 weeks.** Update the client weekly during recovery — not monthly. Ranking velocity, indexation delta, and crawl-stat trends go into a stripped-down white-label reporting view.
6. **Close out.** Recovery sprint closes when organic traffic returns to 80% of pre-drop or after 90 days, whichever comes first. The client converts to ongoing retainer or sunsets cleanly.

## Outputs

- `clients/<client-slug>/recovery/snapshot-v1.md` — pre/post data per cluster.
- `clients/<client-slug>/recovery/triage-plan-v1.md` — diagnosis, scope, projection, disclaimer.
- `clients/<client-slug>/recovery/weekly-log/<iso-week>.md` — weekly recovery updates.
- A closeout memo in `clients/<client-slug>/recovery/closeout-v1.md` with the outcome and retainer recommendation.

## Anti-patterns

- Promising recovery in a fixed number of weeks. Google does not work that way.
- Mass-disavowing referring domains without a documented link-spam diagnosis. Disavow is a last resort.
- Hiding the drop from the client or routing the bad news through anyone other than the account-manager.
- Selling a recovery retainer before confirming the drop is recoverable — taking a recovery fee on a domain that needs replatforming is churn waiting to happen.
- Treating recovery as a content-only or links-only project. The diagnosis sets the lane; the sprint stays in it.

## Reference

Pair this skill with:

- `technical-seo-audit` for the crawl/render/CWV layer of the fix scope.
- `gsc-ga4-reporting-dashboard` for the weekly recovery telemetry.
- `backlink-acquisition-playbook` when the diagnosis points at link-spam exposure.
