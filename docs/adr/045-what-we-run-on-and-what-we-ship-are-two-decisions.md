# ADR-045 — What we run on and what we ship are two decisions

**Status:** Accepted
**Date:** 2026-08-24
**Relates to:** ADR-001 (tech stack; the original model defaults), ADR-017 (per-agent model id
in `.paperclip.yaml`), ADR-014 (resilient JSON generation; structured output),
ADR-043 (whose Open question this closes), ADR-042 (platform-revision posture: say what was
verified and when)

---

## Context

`OPUS_MODEL` and `SONNET_MODEL` were `claude-opus-4-8` and `claude-sonnet-4-6`. The current
generation is Claude Opus 5 and Claude Sonnet 5, and moving to it was the request.

The two constants were doing **two jobs with different authorities**:

1. Through `CONTENT_MODEL` / `STRUCTURAL_MODEL`, they select the model **this tool calls**.
   Validity is decided by our API key and by whether the model accepts this codebase's request
   shape — streaming, adaptive thinking, `output_config.effort`, `output_config.format`. It is
   checkable from this repo.
2. Through `renderers/adapter.py`'s role table, the same strings are emitted as every generated
   agent's `adapter.config.model` in `.paperclip.yaml`. Validity is decided by the operator's
   Paperclip instance and its `claude_local` adapter build. ADR-017 already records that the
   importer does not validate these ids for env-free worker kinds — they are *preferences*, and
   a wrong one fails at agent-run time rather than at import. It is **not** checkable from here.

One pair of constants meant one edit moved both, and nothing anywhere stated they must agree.

## Decision

### 1. The generation-time defaults move to `claude-opus-5` / `claude-sonnet-5`

Verified before the edit by an instrumented call through `LLMClient._invoke_anthropic` — the
production transport, not a hand-rolled request — that both accept the exact request shape this
codebase sends.

### 2. The bundle-facing ids become their own constants

`AGENT_TOP_TIER_MODEL` and `AGENT_BALANCED_MODEL`, read only by `renderers/adapter.py`. They
hold the same strings as the generation-time pair today, and the point of the ADR is that this
is **a coincidence of tiering, not a constraint**.

They live in `config.py` rather than in a new module because `config.py` already hosts a
bundle-facing model id this tool never calls: `CODEX_MODEL`, emitted for the `codex_local`
worker kind. The precedent existed; only the naming had collapsed.

### 3. The separation is enforced structurally, never by comparing values

A test asserting `AGENT_TOP_TIER_MODEL == OPUS_MODEL` would *re-couple* the two and would pass
forever whether or not anything respected the split. The test instead reads
`renderers/adapter.py`'s source and asserts it imports no generation-time constant.

**It fails against the pre-change module** — `adapter.py` imported `OPUS_MODEL` and
`SONNET_MODEL` — which is the evidence that it asserts something. A separation whose crossing
is undetectable is a naming convention, not a decision.

### 4. Structured output was never a no-op — ADR-043's Open question closes, negatively

ADR-043 left open whether `claude-sonnet-4-6` accepts `output_config.format` at all, reasoning
from its absence in a documented support list, and noted that if it did not, `strict_json_schema`
had been silently doing nothing across every structural generator.

**It accepts it, and the constraint binds.** Probed through the production transport with a
schema whose effect is observable in the reply — the prompt asks for prose, so an unconstrained
model answers with a sentence and a constrained one must answer with the object:

| model | request | reply obeys schema |
|---|---|---|
| `claude-sonnet-4-6` | accepted | yes |
| `claude-sonnet-5` | accepted | yes |
| `claude-opus-4-8` (thinking on) | accepted | yes |
| `claude-opus-5` (thinking on) | accepted | yes |

A probe that can only return ACCEPTED would prove nothing, so a control was run first: a schema
carrying an invalid JSON-Schema type keyword returns `400 invalid_request_error` through the
same path and surfaces as `APIRequestError`. The verdicts are therefore informative.

So **ADR-014's claim was right** ("structured output is confirmed for `claude-sonnet-4-6`") and
**ADR-043's inference was wrong**. The general lesson is the one ADR-043 half-stated: a
published support list is evidence about documentation, not about behaviour, and this project
had a cheap way to ask the system itself.

This also means `complete_json`'s schema-dropping fallback path is currently unexercised by any
model in play. It is kept — it is the reason a future model that declines the parameter degrades
instead of failing — but nothing today depends on it, and ADR-043 §3's insistence that the
post-parse `check` run regardless of the schema stands unchanged.

Two incidental observations from the probe, recorded but not acted on: `minLength` (which
`_UNSUPPORTED_SCHEMA_KEYS` strips) is now accepted, and a `required` naming an undeclared
property is accepted without binding. Neither changes anything here.

### 5. The price table stays, and keeps its superseded entries

Whether an internal price table belongs in this codebase at all was asked. It stays, because
**SC-011 of spec 002** requires a completed run to print a token/cost summary — a settled
decision this feature does not reopen. (Checked while asking: no ADR states a
measured-tokens-no-dollar-figure posture, and `api.py` reports neither tokens nor cost.)

What changes is the honesty of the table:

- **Superseded ids are kept**, because the table prices what the tool may be *asked* to call,
  not only its defaults — and because the real-billing reconciliation test anchors to a run made
  on Opus 4.8 and Sonnet 4.6. Repointing that test at the current constants would turn evidence
  into arithmetic: it would assert that today's rates equal themselves.
- **Sonnet 5's introductory rate is deliberately not encoded.** $2/$10 is live through
  2026-08-31, days away as this is written. Encoding it would be right for that week and would
  then under-report every run afterwards with nothing to signal the change. Over-reporting
  during an introductory window is the recoverable direction.
- The table carries the date its figures were verified, and the fall-through is documented as
  the silent failure it is.

### 6. Superseded `--model` aliases are removed, not repointed

Repointing `opus-4.8` at Opus 5 would make the flag say one model and select another. Removed,
the value falls through `resolve_model` unchanged as a literal id and the API reports it, and a
deliberate older-model run stays expressible by full id (`--model claude-opus-4-8`).

## What is not verified

The bundle-facing ids have **not** been checked against a live Paperclip instance: whether a
given `claude_local` adapter build recognises `claude-opus-5` is operator-environment, and
ADR-017 records that the importer does not validate it. This is recorded as unverified rather
than assumed good — it is precisely the asymmetry that motivates §2. An operator whose instance
is pinned to an older adapter can now change the shipped preference without touching what this
tool runs on.

## Consequences

- Five parity baselines and one YAML fixture carried the old ids. They were substituted in place
  for exactly the two strings rather than re-captured: re-capturing would have erased what each
  baseline guards for its own feature. That the substitution was both necessary and sufficient —
  all five went green with no other edit — is itself the proof that the emitted model id is the
  only rendered difference this change makes.
- Test assertions on default models now name the constants instead of literal ids, so they check
  that a generator *routes to the default* rather than restating what the default is.
- ADR-017's role/model table and ADR-043's Open section name superseded ids; both carry a
  pointer here rather than being rewritten.
