---
schema: agentcompanies/v1
slug: brand-voice-capture
name: brand-voice-capture
description: 'Run the 60-minute onboarding voice session that produces a living brand voice document for every Agency Engine retainer client.'
---

# brand-voice-capture

*How Agency Engine captures a client's voice once and defends it forever — the living document the Copywriter, Brand Designer, Video Editor, and channel leads all draw from.*

## When to load this skill

- A new retainer is inside its 14-day onboarding window and the brand voice session has not yet run.
- A QBR is approaching and the quarterly voice refresh is due.
- A creative QA flagged "voice-off" on an external deliverable and the document needs revisiting.
- The client has rebranded, repositioned, or hired new marketing leadership inside the retainer.
- A new channel is added to scope (e.g., adding lifecycle email to a paid-only retainer) and voice must extend to it.

## Inputs

- The signed SOW so the session covers every in-scope channel.
- The discovery brief (Strategist) so we enter with business context, not a blank page.
- Existing client copy samples — emails, ads, web pages, social — for the live-samples block.
- A 60-minute calendar slot with the client's brand decision-maker (founder, head of marketing, or equivalent).
- The Creative Director on the call as session owner; Copywriter as scribe.

## Procedure

The capture session runs 60 minutes. Time-boxed by design — the Creative Director keeps it on rails.

1. **(10 min) Client framing.** Their mission, their customers, what success sounds like to them in their own words.
2. **(15 min) Voice anchors.** Adjectives (pick 5 from a long list), archetypes, three brands they admire and why, three they explicitly are not and why.
3. **(15 min) Live samples.** Walk through real client copy: three pieces they love, three they hate. Reasons captured for each. This is the highest-signal block — verbatim quotes get logged.
4. **(10 min) Forbidden territory.** Words, phrases, claims, comparisons, jokes, and tone shifts they will not say. Captured as a bullet list, not paraphrased.
5. **(10 min) Visual partner.** One-paragraph note on visual voice that pairs with the verbal voice — feeds the Brand Designer.

### Document sections (assembled within 48h of the session)

- **Voice anchors and archetypes** (one paragraph plus adjective list).
- **Approved vocabulary** (≥50 words; sourced from session quotes, not invented).
- **Forbidden vocabulary and forbidden claims** (explicit list; non-negotiable for QA).
- **Sample copy in voice** (3-5 paragraphs the Copywriter drafts and the Creative Director signs off).
- **Visual voice notes** (handed to Brand Designer).
- **Versioning history** (every refresh logged with date, reason, sign-off).

## Outputs

- `clients/<client-slug>/brand/voice-v<n>.md` — the living voice document, versioned on every quarterly refresh.
- A "forbidden territory" block referenced directly by `creative-qa-pipeline` on every external deliverable.
- A visual voice brief filed at `clients/<client-slug>/brand/visual-voice-v<n>.md` for the Brand Designer.
- A session notes file at `clients/<client-slug>/onboarding/voice-session-<YYYY-MM-DD>.md`.

## Anti-patterns

- Voice docs that are pure adjectives with no concrete sample copy — adjectives without samples are unactionable.
- Voice docs that skip forbidden territory — the QA gate then has nothing to enforce against drift.
- Voice changes made mid-cycle without Creative Director sign-off (silent voice drift kills brand consistency).
- Inventing approved vocabulary the client didn't say — every word in the list must trace to a session quote.
- Running the session without the brand decision-maker present (we end up capturing a middle-manager's interpretation).
- Treating the doc as one-and-done — quarterly refresh is part of the QBR cycle, not optional.

## Reference

Pair this skill with:
- `creative-qa-pipeline` — the QA gate that enforces voice on every external deliverable.
- `client-onboarding-sequence` — the 14-day sequence this session sits inside.
- `quarterly-business-review-templates` — the quarterly trigger for voice refresh.
