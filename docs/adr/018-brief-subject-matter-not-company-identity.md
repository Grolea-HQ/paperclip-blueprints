# ADR-018: Brief subject-matter nouns are never the company identity

## Status

Accepted

## Date

2026-06-22

> Sibling to ADR-016 (founder/board naming guard) — the same class of structural
> identity rule, applied to a different bleed: platform/tool names standing in as
> the company.

## Context

A full end-to-end generation on a Paperclip-ecosystem brief (a hypothetical
opportunity-discovery company named **Prospector**, whose brief references the
Paperclip platform, Hermes, OpenClaw, and watchlist repositories heavily as subject
matter) produced a strong, structurally-valid bundle with one repeatable identity
defect: in `agents/ceo/AGENTS.md` the synthesized mandate called the company itself
**"Paperclip"** twice — "the primary owner and final internal orchestrator of
Paperclip's opportunity-discovery engine" and "Decisions to expand or contract the
scope of what Paperclip does or does not do." The company is Prospector. The leak was
isolated to that one file (all eight `SOUL.md` files, `COMPANY.md`, and `OPERATIONS.md`
used "Prospector" correctly), but it is a real, general exposure: **every
Paperclip-ecosystem brief — the tool's core use case — names a platform heavily, and
the synthesis can let the most salient proper noun stand in for the company**,
especially in third-person possessive constructions ("<platform>'s engine", "what
<platform> does").

Root cause, confirmed in the generators: `agents_generator` received the *agent's*
name/title and the company's `we_are`/`north_star` prose, but **never the company's
own name** as a pinned anchor — so with the platform named repeatedly in the brief
prose, the model substituted it as the company referent. `soul_generator` had the same
gap (but first-person persona prose stayed correct); `identity_generator` and
`operations_generator` already received the company name.

This is the same class of structural anti-drift/naming rule as ADR-016 (no
agent name colliding with the human founder/board): a salient noun from the input
bleeding into the company's identity.

## Decision

1. **Pin the company name in every synthesis prompt that produces company-referring
   prose.** `agents_generator` and `soul_generator` now receive `company_name`
   (`company.name`); `identity_generator` (`name`) and `operations_generator`
   (`name`) already had it.

2. **Add a "Company name" rule** to those four prompts (`agents_generator`,
   `soul_generator`, `identity_generator`, `operations_generator`), phrased and placed
   consistently with the ADR-016 naming guard. The rule states: the company is named
   exactly the given name; platforms, tools, runtimes, repositories, and ecosystems
   named anywhere in the brief (Paperclip, Hermes, OpenClaw, GitHub, …) are **subject
   matter the company works with and are never the company**; refer to the company
   only by its own name or a neutral noun phrase ("the company", "this company"),
   never by a platform or tool name and never in a possessive that implies a platform
   owns or is the company.

3. **Tests.** Prompt-content tests assert all four prompts carry the rule (locking it
   in, same pattern as the ADR-016 prompt tests). A gated integration test
   (`@pytest.mark.integration`) generates from a deliberately platform-heavy brief and
   asserts the company's own name appears in each agent's `AGENTS.md` mandate and that
   no platform possessive (`Paperclip's`/`Hermes's`/`OpenClaw's`) appears in
   `COMPANY.md`, the `AGENTS.md` files, or `OPERATIONS.md`.

4. **No hard bundle-gating validator.** A deterministic per-bundle check cannot be
   made non-brittle: a platform name used as the company's possessive ("Paperclip's
   engine") is lexically indistinguishable from a legitimate platform possessive
   ("Paperclip's import format"), and requiring the literal company name in every
   mandate would false-positive on prose that legitimately uses "the company"/"we".
   Per the guardrail, the prompt rule plus the integration assertion is the right
   level; a brittle validator is not shipped.

## Consequences

### Positive
- Every Paperclip-ecosystem brief (the tool's primary use case) is protected from the
  platform-name-as-company bleed, at the actual root cause (a pinned company-name
  anchor in the synthesis prompts).
- Consistent with ADR-016: the company's identity is guarded against salient input
  nouns, whether the human founder/board (016) or a platform/tool (018).

### Negative / limitations
- The guard is prompt-level plus an integration-gated semantic assertion, not a
  deterministic per-bundle gate — by design, because no non-brittle deterministic
  check exists for this defect. A novel phrasing could still slip the prompt rule and
  rely on review.
- The integration assertion runs only under `--integration` with a live API (like the
  other integration tests), so it is not exercised in the default suite.

### Neutral
- `agents_generator`/`soul_generator` now receive one extra prompt variable
  (`company_name`); no new model/field, no new dependency, no `prompts/` restructure.

## Alternatives considered

- **Prompt rule without pinning the company name.** Rejected — weaker, and it ignores
  the actual root cause: `agents_generator` had no company-name anchor, so the rule
  needs a concrete name to bind to.
- **A hard deterministic validator (analogous to I13).** Rejected — too brittle:
  false positives on legitimate platform possessives and on legitimately name-free
  mandates (see Decision 4).

## References

- ADR-016 (founder/board naming guard — sibling structural identity rule),
  ADR-004 (prompt architecture)
- `prompts/{agents_generator,soul_generator,identity_generator,operations_generator}.md`;
  `generators/{agents,souls}.py` (`company_name` wiring);
  `tests/test_prompts.py` (rule-presence), `tests/test_integration_full.py`
  (platform-heavy brief assertion)
