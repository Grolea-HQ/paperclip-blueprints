# ADR-014: Resilient JSON generation — structured output primary, per-leaf retry backstop

## Status

Accepted

## Date

2026-06-14

## Context

`blueprints generate` aborts intermittently with errors like:

```
generation failed: agent mandate response was not valid JSON:
Expecting ',' delimiter: line 2 column 664 (char 665)
```

Every JSON-returning generator asks the model for free-form JSON in its text
response and runs `json.loads` on it (`generators/client.py::parse_json_response`,
plus inline `_parse` in `identity.py`). LLMs occasionally emit slightly malformed
JSON — a missing comma, an unescaped quote inside a string, a stray markdown
fence, a trailing comma, a truncated object. The parse throws `GenerationError`
and the **entire run aborts**, discarding the API spend already paid for identity,
the org plan, and any agents generated before the failure.

This is **non-deterministic** and **scales with company size**: a 14-agent company
makes ~40+ JSON calls (identity, org plan, per-agent mandate + soul, per-skill,
per-project, per-task, operations), so the cumulative probability that *one* of
them is malformed — and kills the whole run — grows with the org. It hits every
user on the core happy path. This is a core-path reliability defect, not
input-defense (the input is fine; the model's *output* varies).

Two independent mechanisms can address it: (1) make a malformed response
non-fatal by re-sampling that single call, and (2) stop malformed JSON from
happening by constraining the model to a schema. They are complementary.

**Verified API facts** (per the Claude API reference, ADR-008 streaming/thinking):

- Anthropic structured outputs constrain the response via
  `output_config={"format": {"type": "json_schema", "schema": {...}}}`, and this
  **composes with `messages.stream()` and `thinking={"type":"adaptive"}`** — the
  existing transport path. `effort` and `format` coexist inside `output_config`.
- JSON-schema limits: `additionalProperties: false` is required on every object;
  numeric/length/pattern constraints are unsupported; `$ref`/`$defs` (nested
  models like `AgentSoul`) are supported. Our Pydantic *field validators*
  (min-items, idle-state belief) are runtime checks, not JSON-schema keywords, so
  they don't appear in the emitted schema and don't trip the limits — they still
  run when we construct the model.
- Structured output is confirmed for `claude-sonnet-4-6` (the structural model).
  It is **not** explicitly confirmed for `claude-opus-4-7` (the content model), so
  the structured path must **degrade gracefully** rather than hard-fail on a model
  that rejects `output_config.format`.

## Decision

Add both tiers at the call/parse boundary (`generators/client.py`), and route
every JSON-returning generator through a single resilient entry point.

### Tier 1 — per-leaf retry + tolerant extraction (backstop, universal)

A new `LLMClient.complete_json(*, model, system, user, what, thinking, effort,
schema=None, attempts=3)`:

1. Calls `complete()` (streams; usage accumulates per attempt — we paid for each).
2. **Tolerant extraction** before parsing (`extract_json_text`): take a fenced
   ```` ```json ```` / ```` ``` ```` block if present, else the outermost `{...}`
   or `[...]` by bracket matching; strip surrounding prose.
3. `json.loads`. On `JSONDecodeError`, re-sample that single call (up to
   `attempts`), appending the parser error to the prompt ("Your previous reply was
   not valid JSON (<err>); return ONLY valid JSON, no prose, no code fence.").
4. On exhaustion, raise `GenerationError` naming the leaf (`what`).

**Per-leaf isolation** falls out of the existing architecture: each generator
call is independent, and the retry lives *inside* the call — identity, the org
plan, and already-generated agents are not regenerated when one leaf re-samples.
Terminal exhaustion still aborts the run (a partial bundle must never be written —
Constitution II), but the common case (a single malformed response) now self-heals
instead of discarding the whole run.

### Tier 2 — structured output (primary, when the model supports it)

`complete()` gains a `schema: dict | None` parameter threaded to the transport;
when set, the transport adds `output_config.format` (alongside `effort` when
thinking is on). Each generator passes a strict JSON schema derived from the
Pydantic model describing its LLM-produced fields, via a new
`strict_json_schema(model, *, include=None, exclude=None)` helper that:

- projects the model's `model_json_schema()` to the included/excluded field set,
- sets `additionalProperties: false` on every object (top-level and `$defs`),
- strips unsupported constraint keywords (`min*`, `max*`, `pattern`, `multipleOf`),
- sets `required` to the emitted property set.

Per generator: identity→`CompanyDefinition`, org→`OrgPlan`,
operations→`OperationsDefinition`, soul→`AgentSoul` (full models);
agents→`AgentDefinition` body fields, skill→`SkillDefinition` minus `slug`,
project→`ProjectDefinition` `{summary, success_condition}`,
task→`TaskDefinition` `{objective, completion_criteria}` (subset models).

**Graceful fallback:** if `complete()` raises `APIRequestError` (the SDK's
`BadRequestError`, e.g. a model that rejects `output_config.format`),
`complete_json` drops the schema and continues with Tier 1 retry for the remaining
attempts. So structured output is used wherever available and the prompt-JSON +
retry path covers everything else. The Pydantic model is still constructed after
parsing, so all semantic validators (≥1 skill, idle-state belief, anti-drift
echo) run regardless of which path produced the JSON.

## Consequences

### Positive
- A single malformed response no longer aborts a whole run; the common failure is
  invisible to the user.
- On structured-output-capable models, the malformed-JSON class is nearly
  eliminated at the source.
- One resilient entry point (`complete_json`) replaces the scattered
  `complete()` + `parse_json_response()` pairs, so the behavior is uniform and
  testable in one place.
- No new dependency — the Anthropic SDK already supports structured output.

### Negative / trade-offs
- Retries cost extra tokens when they fire (acceptable — far cheaper than
  discarding a whole run; usage tracking already counts them).
- Strict schemas must track the models; a schema that over-constrains could be
  rejected by a model — mitigated by the graceful fallback to the retry path.
- Terminal exhaustion still fails the run (by design — no partial bundles).

### Neutral
- `attempts=3` (1 initial + 2 retries) is policy, tunable without structural change.
- `bundle.py`'s `asyncio.gather` fan-out is unchanged: a leaf that exhausts
  retries propagates as today, but the common transient failure is now resolved
  in-leaf before it ever reaches `gather`.

## Alternatives considered

- **Retry-only (no structured output).** Rejected as the *sole* fix: it makes
  failures invisible but doesn't stop them; structured output removes the class at
  the source where supported. Retry is kept as the backstop.
- **Structured-output-only (no retry).** Rejected: not confirmed on the Opus
  content model, and a backstop is needed for any model/path that rejects or
  mis-emits under the format. Retry must stay.
- **`messages.parse()` with Pydantic.** Rejected: our generators construct domain
  models from field *subsets* merged with stub data (agent body, project body,
  …) and run custom validators; raw schema-constrained JSON + existing
  construction fits that shape better than SDK-side parsing into the full model.
- **Forcing tool use (`tool_choice`).** Rejected in favor of
  `output_config.format` — same guarantee for "return one schema-valid object",
  no synthetic tool to define per call, composes cleanly with streaming + thinking.

## References

- ADR-004 (prompt architecture), ADR-008 (adaptive thinking / streaming),
  ADR-001 (no new dependencies)
- `generators/client.py` (the call/parse boundary), the eight JSON generators
- Claude API reference: structured outputs (`output_config.format`), streaming +
  extended-thinking compatibility, JSON-schema limitations

## Out of scope (recorded so they are not chased)

- No input validators for this — it is model-output variance, not bad input.
- No change to the budget allocator (ADR-012), bundle shape, or import-fidelity
  work (ADR-013).
