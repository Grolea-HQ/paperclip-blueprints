---
schema: agentcompanies/v1
slug: newsletter-voice-capture
name: newsletter-voice-capture
description: 'Extracting and codifying the founder''s voice from drafts, edits, and voice memos into a one-page guide and banned-phrase list every agent on the masthead can apply — because the founder''s voice is the moat.'
---

# newsletter-voice-capture

*How Newsletter Press turns the founder's drafts into a usable voice guide that any agent on the masthead can apply on first wake, without re-reading five issues.*

## When to load this skill

- Before editing any issue draft for the first time as a new agent on the editorial loop (Managing Editor, Staff Writer, Repurpose Editor, Paid Tier Manager, Cross-Promo Lead).
- After every fourth send — voice drifts gradually and the guide needs a refresh on a known cadence.
- When the founder rewrites an agent draft and the changes reveal a pattern not yet captured.
- When onboarding a new agent into the editorial loop and the calibration sheet is the first thing they read.
- When a subject-line winner reveals a frame the founder uses naturally but the guide has not codified.

## Inputs

- Five recent issues the founder wrote without heavy edits. If five do not exist yet, supplement with podcast transcripts, long-form social posts, or voice-memo transcriptions tagged in `editorial/founder-memos/`.
- The last twenty agent drafts the founder edited, with the edits visible (track changes, comments, or git diff). The "edited out" content is the actual moat.
- The current `editorial/voice-guide.md` and `editorial/banned-phrases.md` for diff continuity.

## Procedure

1. **Collect five clean samples.** Pull the last five issues the founder wrote without heavy editorial intervention. Mixed-author issues do not count — voice is captured from the founder alone.
2. **Tag voice markers, sample by sample.** For each, mark:
   - **Sentence rhythm.** Long-short-long. Short-staccato. Em-dash interruption. Note the pattern.
   - **Preferred verbs.** The verbs that recur across samples are voice; one-off verbs are noise.
   - **Opening hooks.** What grabs attention in the first sentence? Question, contrarian claim, concrete number, anecdote?
   - **Sign-offs.** How does the founder close — "talk soon," "more next week," a question, nothing?
   - **Banned words.** Words present in agent drafts but absent across all five founder samples.
3. **Build the diff sheet.** Two columns: phrases the founder uses naturally; phrases the founder has edited *out* of agent drafts. The edited-out column is the load-bearing artifact. It is what protects the moat.
4. **Write the voice guide.** One page. Three sections, in this order:
   - *What the voice sounds like* — three to five concrete rhythmic descriptions, each with a quoted example.
   - *What it never sounds like* — three to five concrete anti-examples.
   - *The ten phrases you should never use* — exact strings, no paraphrase, sourced from the diff sheet.
5. **Store at `editorial/voice-guide.md` and `editorial/banned-phrases.md`.** Reference the slug in every editorial AGENTS.md (Managing Editor, Staff Writer, Repurpose Editor, Paid Tier Manager).
6. **Re-run on cadence.** Every four sends, repeat steps 1–5 with the newest five samples. Old samples roll out; the guide stays current with where the founder's voice is now, not where it started.

## Outputs

- `editorial/voice-guide.md` — one-page calibration sheet. Title, three sections, concrete examples.
- `editorial/banned-phrases.md` — flat list of exact strings, one per line, that any agent drafting under the masthead must strip before submitting.
- `editorial/voice-diffs/<YYYY-MM>.md` — quarterly diff record showing what changed in the guide and why.

## Anti-patterns

- Voice guides written as marketing copy — "authentic, warm, authoritative." Useless. Write the actual rhythm.
- Voice guides longer than one page. Agents will not re-read them, and the calibration value drops to zero.
- Voice guides built from one sample. The pattern is in the diff between samples, not in any single one.
- Letting the banned-phrases list grow past 30 entries. Pruning is required — old banned phrases that have not appeared in a draft for two quarters get retired.
- Pulling voice samples from heavily edited founder drafts. The voice you capture is the editor's, not the founder's.
- Treating the voice guide as static. The founder's voice drifts; the guide refreshes every four sends or the moat decays.

## Reference

Pair this skill with:
- `editorial-calendar` — angles get rejected at the calendar stage if they cannot be written on-voice.
- `issue-repurposing-to-threads` — the Repurpose Editor self-grades against the artifacts produced here.
