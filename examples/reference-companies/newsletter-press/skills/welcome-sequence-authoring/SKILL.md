---
schema: agentcompanies/v1
slug: welcome-sequence-authoring
name: welcome-sequence-authoring
description: 'Writing the five-email welcome sequence that turns a new free subscriber into a paid-trial start within 14 days, in the founder''s voice — the highest-leverage copy in the company, because it is where free-to-paid conversion is won or lost.'
---

# welcome-sequence-authoring

*How Newsletter Press writes the five welcome emails every new free subscriber receives — in the founder's voice, because this is the highest-leverage copy in the business.*

## When to load this skill

- The newsletter is launching and the welcome sequence has not yet been authored.
- The Paid Tier Manager flags that free-to-trial conversion has fallen below 2.0% for two consecutive weeks.
- The Cohort Churn Analyst's monthly table shows a Day-30 retention dip that points back to onboarding.
- The founder records a new origin story and email #2 needs to be re-written off the new source material.
- The ESP is changing (Substack → beehiiv, etc.) and the sequence needs to be re-implemented in the new automation.
- A pricing change has been approved by the CEO and email #4 needs to be rebuilt against the new offer.

## Inputs

- `editorial/voice-guide.md` — the founder's voice, in one page, plus banned phrases.
- A founder-recorded origin story (audio or written) for email #2. Without this, the sequence cannot ship — email #2 is the founder, not the agent.
- The current paid-tier price points from `operations/esp/config.md`.
- One "banger" past issue chosen by the CEO for email #1's reference link.
- The current free-to-trial conversion baseline from `paid-tier-conversion-funnel`, so the rewrite has a ground truth to measure against.

## Procedure

### Sequence map — fixed structure

| # | Sent | Purpose | Soft-pitch level | Author |
|---|---|---|---|---|
| 1 | Immediately on signup | Welcome, set cadence expectation, link to one banger past issue | None | Paid Tier Manager → Managing Editor voice review |
| 2 | Day 2 | Founder's origin — why this newsletter exists | None | **Founder writes personally**, no exceptions |
| 3 | Day 4 | One free deep-dive piece, establishes the value bar | Footer mention of paid tier | Paid Tier Manager → Managing Editor voice review |
| 4 | Day 7 | "Here's what the paid tier unlocks" — concrete examples, not feature lists | Strong pitch | **Founder writes personally**, no exceptions |
| 5 | Day 14 | Trial offer — 14-day free trial of the paid tier with a direct CTA | Direct CTA | Paid Tier Manager → Managing Editor voice review |

### Authoring loop

1. **Read the latest five issues.** The welcome sequence is the founder's voice in concentrated form; if you cannot hear the rhythm yet, start in `newsletter-voice-capture`, not here.
2. **Draft emails 1, 3, and 5.** These are the Paid Tier Manager's authoring scope.
3. **Bring drafts to Managing Editor voice review.** Drafts that fail voice review go back, not forward.
4. **Founder writes emails 2 and 4 personally.** Email 2 is identity; email 4 is the paid-tier ask. Both must read as the founder, not as the company.
5. **Wire the automation in the ESP.** Trigger on free-signup event; timing exactly as the sequence map specifies. The Newsletter Producer ships the automation.
6. **Instrument every email.** Open rate, click-through, trial-start attribution. Numbers flow into `paid-tier-conversion-funnel`.
7. **Re-author on signal, not on schedule.** Do not sweep the sequence every quarter for the sake of it. Change one email at a time when the funnel says it is the worst stage.

## Outputs

- `editorial/welcome-sequence/email-1.md` through `email-5.md` — final copy with subject lines, preheaders, and personalization fields declared.
- `operations/esp/automation-welcome.md` — the ESP automation spec: trigger, delays, segment exits.
- A one-page CEO-readable launch note: which emails the founder wrote personally, when the sequence went live, baseline free-to-trial conversion.

## Anti-patterns

- "Welcome to our community!" — not how the founder speaks. Banned.
- "We're so excited to have you" — banned. Reads as marketing, not voice.
- Generic curiosity hooks not tied to the founder's actual point of view. The voice is the moat; cold-tested hooks bypass it.
- Allowing email 2 or email 4 to ship without the founder writing it personally. The sequence converts because subscribers hear the founder; outsourcing those two emails is the single fastest way to break the funnel.
- Quarterly sweep rewrites of the whole sequence. The funnel signal does not survive simultaneous changes — see `paid-tier-conversion-funnel`.
- Sending the welcome sequence to imported lists. The sequence assumes a fresh signup event; on imported subscribers it reads as a stranger's introduction and torches the sending domain reputation.
- Discounting in email 5 to "boost trial starts." Pricing only changes with CEO approval; trial sweeteners that are not on the rate sheet are not the Paid Tier Manager's call.

## Reference

Pair this skill with:
- `paid-tier-conversion-funnel` — the measurement layer that decides which email needs a rewrite.
- `newsletter-voice-capture` — the upstream voice guide every draft is graded against.
