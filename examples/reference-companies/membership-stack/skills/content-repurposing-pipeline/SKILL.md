---
schema: agentcompanies/v1
slug: content-repurposing-pipeline
name: content-repurposing-pipeline
description: 'How one Monday release becomes a community thread, an email, three-to-five social posts, and a short-form video clip — without re-typing copy for every surface, so content velocity scales without burning out the content team.'
---

# content-repurposing-pipeline

*One source, many surfaces. The Monday release is the well; everything else is a tap on it.*

## When to load this skill

- A Monday release has been approved by the Content Director and the repurposing window opens.
- The Community Manager needs the community thread copy for the 09:30 Monday post.
- The CMO is assembling the Monday-12:00 promotion (email + social) and needs atomic notes pulled.
- The Video Producer is deciding whether a release supports a short-form clip.
- A scheduling conflict suggests we should "promote later" — the pipeline's surface order needs to be re-confirmed.

## Inputs

- The approved source artifact (Monday's template, guide, tool, or video release).
- The Content Director's 5–8 atomic notes (one idea per note, 1–3 sentences each).
- The atomic-note tagging schema: source release slug, suggested surfaces, member-only flag.
- The current Monday surface order: community → email → social → video clip (Tuesday onward for externals).

## Procedure

1. **Friday filing.** Writer or Video Producer files the source artifact with the Content Director (this is the same handoff that gates the Monday release).
2. **Content Director extracts atomic notes.** 5–8 notes, one idea each, 1–3 sentences. Each note carries its source release slug, suggested surfaces, and a member-only boolean.
3. **Community thread.** Community Manager builds one community thread from the highest-resonance note(s). Posted at 09:30 Monday.
4. **Email blast.** Writer drafts a single member-facing email keyed to the release's headline note. CMO sends Monday 12:00.
5. **Social posts.** CMO selects 3–5 atomic notes flagged "ok to publicize" (no member-only) and writes one social post per note. Externals run Tuesday onward — never before the community sees it.
6. **Short-form video clip.** Video Producer evaluates whether the format supports a 30–60s clip. If yes, cut and queue. If no, skip — we never force a clip that doesn't earn it.

## Atomic note schema

```
note:
  source_release: <release-slug>
  text: <1-3 sentence idea>
  suggested_surfaces: [community, email, social, video]
  member_only: <true|false>
```

## Outputs

- `library/_repurposing/<release-slug>/atomic-notes.md` — the 5–8 notes with tags.
- The community thread (Community Manager), email blast (Writer → CMO sends), 3–5 social posts (CMO), and optional short-form video clip (Video Producer).
- A repurposing-coverage entry in `analytics/release-log.md` so the Retention Analyst can correlate surface count against MRR additions by source.

## Anti-patterns

- Repurposing a draft release — repurposing happens only after Content Director approval.
- Promoting externally before community posts go live on Monday — members hear it first.
- Pushing member-only content into public channels without an explicit "ok to publicize" tag — we don't leak proprietary library content into the open web.
- Re-writing copy for every surface from scratch — the pipeline exists exactly to prevent this. If a surface needs net-new copy, the atomic-note step was skipped.
- Forcing a short-form video clip when the source doesn't support it — the Video Producer's call, not the CMO's.
- Layering an annual upsell or affiliate push into the email — Monday emails are about the release, not about conversion campaigns. Conversion runs on its own calendar.

## Reference

Pair this skill with:
- `content-release-calendar` for the Monday rhythm the pipeline rides on.
- `affiliate-program-setup` for why affiliate content runs on a separate cadence, not on top of release emails.
