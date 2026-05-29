---
schema: agentcompanies/v1
slug: creative-qa-pipeline
name: creative-qa-pipeline
description: 'Run the written QA checklist on every external Agency Engine deliverable before the Account Manager touches it.'
---

# creative-qa-pipeline

*How Agency Engine keeps the craft bar high on every external piece — the written checklist the Creative Director enforces between production and the Account Manager.*

## When to load this skill

- A Brand Designer, Copywriter, or Video Editor is about to submit an external deliverable.
- The Creative Director is running a QA pass on submitted work before client handoff.
- A Project Manager is checking Run-week outputs against the cycle's Plan-week plan.
- A Reporting Engineer is validating the visual presentation of the monthly client report pack.
- An external deliverable came back from the client flagged "off" and a QA forensic is needed.

## Inputs

- The Plan-week brief defining objective, audience, channel, and format.
- The current brand voice document from `brand-voice-capture`.
- The signed SOW so scope can be verified per deliverable.
- The client's visual system files (logo, palette, type, layout grids).
- Rights-and-licensing receipts for any third-party assets (music, footage, stock imagery).

## Procedure

The Creative Director runs the checklist top-to-bottom. Each item is a pass/fail with a one-line note. If any item fails, the piece returns to the producer with the named fail; it does not advance to the Account Manager.

1. **Brief alignment.** Does the deliverable match the brief's objective, audience, channel, and format?
2. **Brand voice fit.** Does the copy / visual / cut live inside the captured voice document? No forbidden vocabulary, no forbidden claims.
3. **Visual system fit.** Does it use the client's visual system — not a generic template, not a stock layout?
4. **Scope check.** Is this deliverable named in the signed SOW for this cycle? If not, route to `scope-creep-recovery`.
5. **Commercial-claim check.** Pricing, guarantees, comparisons, performance claims — any of these triggers a mandatory CEO sign-off before send.
6. **Rights and licensing.** Music, footage, imagery, fonts — all cleared, logged, and license terms filed.
7. **Channel-format compliance.** Aspect ratios, character limits, platform-specific specs (e.g., Instagram Reels 9:16, Klaviyo subject ≤ 60 chars, LinkedIn carousel 1080×1080) respected.
8. **Inventory check.** Not duplicating an existing deliverable already in `PROJECT-INVENTORY.md`.
9. **Sign-off log.** QA passed by Creative Director with date and one-line summary filed.

### Producer self-QA (run before submission)

- **Pre-submission read-aloud.** Copywriter reads copy aloud; if it sounds stilted, it does not ship.
- **Pre-submission frame-pass.** Brand Designer pulls every layout at 100% zoom; rounds typographic and grid errors before submission.
- **Pre-submission silent watch.** Video Editor watches the cut with sound off; if the visual story doesn't carry, sound design is masking craft gaps.

## Outputs

- A signed-off deliverable filed at `clients/<client-slug>/deliverables/<cycle>/<asset-id>.md` with QA receipt block appended.
- A QA receipt log entry at `clients/<client-slug>/qa/<YYYY-MM>.md` per deliverable.
- A licensing log at `clients/<client-slug>/licensing/<asset-id>.md` for every third-party-asset deliverable.
- A `scope-creep-recovery` route triggered for any deliverable that fails the scope check.

## Anti-patterns

- Verbal "looks good" approvals — every external piece passes the written checklist; nothing else counts.
- QA skipped for "small" social posts — small pieces fail visibly, and the cadence depends on every piece being on-brand.
- Commercial-claim copy approved without CEO sign-off — legal and brand exposure compounds silently.
- Using a generic template "for speed" instead of the client's visual system — kills the differentiation the retainer is paying for.
- Treating the inventory check as optional — duplicate deliverables across cycles burn client trust.
- Shipping a piece without the rights-and-licensing log — exposure surfaces months later in a takedown.

## Reference

Pair this skill with:
- `brand-voice-capture` — the voice document this checklist enforces.
- `scope-creep-recovery` — the route when the scope check fails.
- `monthly-strategy-review` — the brief this checklist measures alignment against.
