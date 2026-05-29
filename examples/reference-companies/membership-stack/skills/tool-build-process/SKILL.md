---
schema: agentcompanies/v1
slug: tool-build-process
name: tool-build-process
description: 'How the Tool Engineer scopes, builds, and ships lightweight library tools — calculators, embedded scripts, single-page webapps — without sliding into a SaaS engineering cycle the team cannot operate at scale.'
---

# tool-build-process

*Lightweight tools, not micro-SaaS. Every tool returns a result in under 60 seconds; nothing we ship runs a database of member data.*

## When to load this skill

- The Tool Engineer owns a week-3 Monday slot and is scoping the next tool.
- A member request or quarterly survey "wish we had" theme suggests a chore worth automating.
- The Product Manager is reviewing whether a proposed tool meets the lightweight bar.
- A tool's "next refresh due" date is approaching and a sustaining release is being planned.
- The Platform Engineer flags that a tool's hosting surface is being deprecated by its vendor.

## Inputs

- The one-line job-to-be-done the tool solves.
- The intended inputs from a member, listed concretely.
- The single output artifact the tool produces (a number, a chart, a downloadable file, a copyable text block).
- A target time-to-result for the member (must be under 60 seconds from open to result).
- A managed hosting surface (Vercel, Apps Script, Notion, GitHub Pages, etc.) — never a bespoke VPS.

## Procedure

1. **Scope before any code.** All five inputs must be answered: job-to-be-done, inputs, output, time-to-result, hosting plan. If any are missing, the tool isn't scoped yet — go back to scoping.
2. **Build as a single deploy unit.** One file or one repo. No multi-service tools, no companion backend.
3. **No accounts, no logins, no member data persisted server-side.** Tools are stateless. Membership entitlement is checked at the library link layer (before the member ever reaches the tool), not inside the tool.
4. **Build the failure path.** If an input is malformed or a third-party API errors, the tool returns a clear, human-readable message — not a stack trace.
5. **Write the INDEX.md and release-notes.md.** Same standard as a template (see asset-library-architecture). Include the hosting URL, the inputs schema, the output type, and the "next refresh due" date.
6. **Hand to Product Manager for review.** PM checks scope, hosting plan, and the 60-second time-to-result claim. CEO approves the release into the week-3 slot.
7. **File the maintenance note.** Tool Engineer records the "next refresh due" date in the asset's `INDEX.md` — typically 6 months out, sooner if the tool depends on a third-party API.

## Outputs

- `library/tools/<category>/<tool-slug>/` containing the deploy artifact (or link), `INDEX.md`, `release-notes.md`.
- A hosting record (which managed surface, which account, which renewal/billing concern).
- A "next refresh due" entry in the maintenance log so the tool doesn't silently rot.
- A line in the weekly cohort report under "content velocity" and "library count".

## Anti-patterns

- Building a tool that requires us to operate a database of member data — entitlement check happens at the library layer, never inside the tool.
- Standing up a bespoke VPS for a single tool — managed hosting only. We do not become an infrastructure operator.
- Depending on a free-tier API the vendor can yank without notice (no grace period, no SLA) — if the API disappears, the tool dies, and members notice.
- Multi-repo or multi-service tools — one deploy unit per tool. Anything more belongs in a different company.
- Tools that exist to "show off engineering" — every tool solves a chore in under 60 seconds; demos are not the bar.
- Shipping a tool without a "next refresh due" date — un-tracked tools become silently-broken tools.
- Adding logins or persistent state mid-version to "fix" a UX problem — that breaks the lightweight contract and forces operational load the team cannot carry.

## Reference

Pair this skill with:
- `asset-library-architecture` for where the tool lands and how `INDEX.md` is filled.
- `template-design-standards` for the parallel quality bar on template-type assets.
