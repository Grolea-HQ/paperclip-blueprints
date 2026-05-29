---
schema: agentcompanies/v1
slug: client-onboarding-sequence
name: client-onboarding-sequence
description: 'Run the 30-day SEO Bureau retainer onboarding — kickoff, access provisioning, baseline audit, dashboard setup, and first deliverable shipping — without leaking into the first month''s retainer.'
---

# client-onboarding-sequence

*How SEO Bureau onboards a new retainer client across the first 30 days so the first monthly white-label report ships on the first business day of the following cycle.*

## When to load this skill

- A new ongoing retainer ($2.5K–$8K/month) or recovery retainer ($6K–$12K/month) has been signed.
- An audit-tier client has converted to an ongoing retainer and the onboarding clock restarts.
- A partner agency has signed a white-label retainer and the SEO Bureau onboarding sits behind their client-facing brand.
- The Head of Accounts flags an in-flight onboarding as drifting past day 21 without a first deliverable.

## Inputs

- Countersigned engagement letter naming tier, scope, deliverables, branded vs. white-label mode, and escalation paths.
- Productized service tier confirmation (audit, ongoing, or recovery) so the deliverable cadence matches the retainer math.
- Client stakeholder map: economic buyer, day-to-day contact, publisher, and access-grant owner.
- Reporting-engineer's availability for baseline GSC + GA4 snapshot inside the first 10 days.

## Procedure

### Day 0–3: kickoff

1. **Schedule the kickoff call inside 3 business days** of signature. Account-manager leads; tech-seo-lead and content-strategist attend.
2. **Confirm the engagement letter on the call**: tier, scope, deliverables, branded vs. white-label reporting, escalation path, retainer math (no retainer below $2.5K/month).
3. **Lock the stakeholder map** in `clients/<client-slug>/onboarding/stakeholders-v1.md`: who decides, who publishes, who grants access.

### Day 3–10: access and baseline

1. **Provision access.** GSC (full), GA4 (read), CMS (read only — we brief and recommend; we do not publish), rank tracker, hosting (only if a render or log-file audit is in scope).
2. **Baseline snapshot.** Reporting-engineer pulls GSC + GA4 baseline numbers and writes `clients/<client-slug>/reporting/baseline-v1.md`. These become the MoM comparison set for every white-label report.
3. **Dashboard creation.** Set up the GSC + GA4 dashboard in branded or white-label mode per the engagement letter. Hybrid mode requires explicit CEO approval.

### Day 10–21: first audit deliverable

1. **Technical SEO audit.** Tech-seo-lead runs the audit using the `technical-seo-audit` skill. Output lands in `clients/<client-slug>/audits/technical-v1.md`.
2. **Content cluster plan.** Content-strategist scopes the pillar-and-cluster map in `clients/<client-slug>/content/cluster-plan-v1.md`.
3. **Link approved-source list.** Link-acquisition-lead drafts `clients/<client-slug>/links/approved-sources-v1.md`. CEO approval required before any outreach.

### Day 21–30: shipping mode

1. **First retainer cycle starts.** Briefs, fixes, and outreach run under the agreed productized service tier scope.
2. **First white-label monthly report scheduled** for the first business day of the next full month.
3. **30-day check-in.** Account-manager + CEO + client review onboarding quality. Any misalignment is named and resolved before it becomes a churn risk.

## Outputs

- `clients/<client-slug>/onboarding/stakeholders-v1.md` — stakeholder map.
- `clients/<client-slug>/reporting/baseline-v1.md` — baseline GSC + GA4 numbers.
- `clients/<client-slug>/audits/technical-v1.md` — first technical audit.
- `clients/<client-slug>/content/cluster-plan-v1.md` — first content cluster plan.
- `clients/<client-slug>/links/approved-sources-v1.md` — CEO-approved link source list.
- White-label or branded dashboard live in the reporting stack.
- Day-30 onboarding review note in `clients/<client-slug>/onboarding/day-30-review.md`.

## Anti-patterns

- Slipping the first monthly white-label report because onboarding ran long. The report ships on the first business day regardless.
- Granting write access to the client CMS. We brief, we recommend, the client publishes — protecting the boundary protects the retainer.
- Starting outreach before the CEO signs the approved-source list.
- Onboarding without a countersigned engagement letter. Verbal scope creates retainer-math arguments.
- Running the kickoff without tech-seo-lead and content-strategist present. The client should never explain the same thing twice.
- Letting Day-30 pass without a check-in. Silent retainers churn at month 3.

## Reference

Pair this skill with:

- `technical-seo-audit` for the Day-10–21 audit.
- `gsc-ga4-reporting-dashboard` for the baseline + dashboard.
- `white-label-reporting-pack` for the first monthly report.
