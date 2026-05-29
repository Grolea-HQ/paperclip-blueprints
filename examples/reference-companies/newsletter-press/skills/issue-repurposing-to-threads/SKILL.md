---
schema: agentcompanies/v1
slug: issue-repurposing-to-threads
name: issue-repurposing-to-threads
description: 'Extracting LinkedIn long-form posts and X threads from each newsletter issue after every send and queuing them across seven days so the inbox stays home base while social acts as a feeder, without diluting the founder''s voice.'
---

# issue-repurposing-to-threads

*How Newsletter Press turns one weekly issue into a week of LinkedIn and X posts — autonomously, on-voice, and without ever leaking subscriber-only content.*

## When to load this skill

- An issue just shipped through the Newsletter Producer and the post-send autonomous loop has fired.
- A past issue is being re-promoted because a sponsor or partner asked for amplification on a specific date.
- The Repurpose Editor's voice self-grade has flagged drift and the queue needs a rewrite pass.
- The Growth Lead is auditing the feeder channels and the repurposing log needs reconciliation.

## Inputs

- The just-sent issue, including the paid-block boundary marker (everything below the marker is subscriber-only and never repurposed).
- `editorial/voice-guide.md` — the same voice guide that gated the original send.
- `editorial/banned-phrases.md` — extracted from `newsletter-voice-capture`. The Repurpose Editor self-grades against this list.
- The social queue file at `distribution/social-queue.md` — current scheduled posts so the new content does not collide with old.
- The repurposing log at `distribution/repurposing-log.md` — every prior thread for the issue, so we do not double-post.

## Procedure

1. **Read the issue twice.** Once for the argument. Once for the three sentences that could stand alone outside the surrounding paragraph. Those three sentences are the spine of the week's social.
2. **Honor the paid boundary.** Anything below the paid-block marker does not get repurposed — ever. If the issue was a paid-only edition, only the headline frame and a soft "subscribers got…" tease may surface on social.
3. **Pick one frame per platform.**
   - **LinkedIn:** long-form post, 150–250 words, single argumentative spine, optional quote card. No external link in the first comment trick; we link to the issue directly.
   - **X:** 5–8 tweet thread. Tweet 1 carries the opening hook (verbatim from the issue when possible). Tweets 2–6 carry the meat. The closing tweet links to the free issue page on Substack / beehiiv / ConvertKit.
4. **Voice-match every draft.** Run each piece against the voice guide. Strip any phrase on the banned list. If the draft does not pass the self-grade, do not ship — defer to Managing Editor.
5. **Schedule across seven days.**
   - LinkedIn: day +1, day +3, day +5.
   - X: day +1, day +2, day +4, day +6.
   - The send day itself is reserved for the issue.
6. **Log to `distribution/repurposing-log.md`.** One row per post: platform, send time, source paragraph, voice self-grade outcome, click-through to the issue.

## Outputs

- `distribution/social-queue.md` — populated with the next seven days of scheduled posts.
- `distribution/repurposing-log.md` — append-only history with per-post engagement once the post lands.
- A weekly one-line summary into the Growth Lead's roll-up: posts shipped, click-through to the issue, top performer.

## Anti-patterns

- Repurposing the paid block. Subscriber-only content stays subscriber-only — that is the deal we sell.
- Running the repurposing loop through CEO approval. This is the one autonomous workflow; the source material was approved at send time, and re-approving every spin-off is the kind of work that strangles cadence.
- Posting the same hook on both platforms verbatim. LinkedIn and X readers overlap enough that double-posting reads as automation, not voice.
- Inventing a new argument on social that was not in the issue. Social is a feeder for the inbox, not a parallel publication.
- Cross-posting surveys to LinkedIn or X. Surveys live in the issue, not on social, so reply rates do not get diluted by drive-by replies.
- Re-promoting an issue more than twice within 60 days. The feed reads as stale and the founder's voice degrades into greatest-hits packaging.

## Reference

Pair this skill with:
- `newsletter-voice-capture` — the source of the voice guide and banned-phrase list.
- `editorial-calendar` — where the original angle was vetted before it became repurposable material.
