# ADR-008: Adaptive thinking replaces fixed-budget thinking on Opus calls

## Status

Accepted

## Date

2026-05-30

## Context

Content-synthesis calls (`identity_generator`, `soul_generator`) run on Opus
with extended thinking enabled — see ADR-004. The original implementation
requested thinking with the legacy fixed-budget shape:

```python
thinking={"type": "enabled", "budget_tokens": 4000}
```

As of Claude Opus 4.7, Anthropic removed the legacy fixed-budget thinking API.
The call now fails at runtime with HTTP 400:

> `thinking.type.enabled is not supported for this model. Use
> thinking.type.adaptive and output_config.effort to control thinking behavior.`

This surfaced when running `blueprints preview`. The model now sizes its own
reasoning; the caller controls depth via an effort level rather than a token
budget. We were also still pinned at `anthropic>=0.40`, an open lower bound that
let the resolved SDK drift between installs.

## Decision

1. Switch the thinking shape in the single API seam
   (`generators/client.py::LLMClient`) from fixed-budget to adaptive:

   ```python
   thinking={"type": "adaptive"}
   output_config={"effort": effort or "high"}
   ```

2. Make `effort="high"` the project default for thinking-enabled
   (content-synthesis Opus) calls. The default is resolved once, in
   `complete()`, so every current and future thinking call inherits it without
   repeating the literal. Callers may override with an explicit `effort=`.
   `identity_generator` and `soul_generator` both pass `thinking=True` with no
   explicit effort and therefore run at `high` — both produce identity-quality
   content that agents read on every wakeup.

3. Leave the Sonnet structural calls (`org_planner`, `agents_generator`,
   `skill_generator`) untouched: they never enable thinking, so they send
   neither `thinking` nor `output_config`. A guard test locks this contract so
   expensive reasoning can't be switched on for cheap-tier calls by accident.

4. Pin the SDK exactly: `anthropic==0.105.2` (was `anthropic>=0.40`), and
   refresh `uv.lock`. Upgrades become an intentional, reviewed act — same
   discipline spec-kit applies to its own pins.

## Consequences

### Positive consequences

- `preview` and `generate` work again on Opus 4.7+; we are forward-compatible
  with the current thinking API.
- The content-synthesis effort default (`high`) lives in exactly one place; new
  v0.1b thinking calls (e.g. `operations_generator`) inherit correct behavior
  for free.
- The exact SDK pin means a future Anthropic API shape change is caught at an
  intentional upgrade, not silently at the next `uv sync`.
- The guard test prevents accidentally enabling adaptive thinking (and its cost)
  on the Sonnet structural tier.

### Negative consequences

- Bumping the SDK is now a deliberate edit-and-relock step, not automatic.
- We no longer cap thinking tokens directly; cost per content call is governed
  by the effort level and the model's own sizing rather than a hard budget.

### Neutral consequences

- CLAUDE.md's tech-stack note — "use the extended-thinking feature on Opus calls
  for content synthesis" — remains semantically true; only the wire shape
  changed. No CLAUDE.md edit (which would itself need an ADR) is required.
- `_THINKING_BUDGET` is removed from `client.py`; `_MAX_TOKENS` stays.

## Alternatives considered

- **Keep fixed-budget thinking.** Rejected: the API no longer accepts it on
  Opus 4.7+; the call hard-fails with 400.
- **Per-call effort literals in `identity.py` / `souls.py`.** Rejected: the
  high default belongs in one place so future thinking calls inherit it. Explicit
  per-call `effort=` remains available as an override.
- **Keep the open `>=0.40` lower bound.** Rejected: it let the SDK drift between
  installs; this very break would have been invisible until it bit at runtime.

## References

- ADR-004 — prompt architecture (which calls use Opus + thinking)
- `src/paperclip_blueprints/generators/client.py` — the single API seam
- Anthropic API: adaptive thinking + `output_config.effort`
