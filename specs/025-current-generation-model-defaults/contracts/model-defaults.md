# Contract — model defaults and the generation/bundle split

Postconditions the test suite asserts. Clause ids are cited from tests.

## C1 — Generation-time selection

- **C1.1** `CONTENT_MODEL == "claude-opus-5"`.
- **C1.2** `STRUCTURAL_MODEL == "claude-sonnet-5"`.
- **C1.3** Every content generator (identity, souls, operations) dispatches its call with
  `CONTENT_MODEL` when the caller passes no `model`.
- **C1.4** Every structural generator (org, agents, skills, projects, tasks, goal hierarchy)
  dispatches with `STRUCTURAL_MODEL` when the caller passes no `model`.

## C2 — Import-time preference

- **C2.1** `assign_adapters` maps `owner` to `AGENT_TOP_TIER_MODEL` and `manager`,
  `engineering`, `generic` to `AGENT_BALANCED_MODEL`.
- **C2.2** `AGENT_TOP_TIER_MODEL == "claude-opus-5"` and
  `AGENT_BALANCED_MODEL == "claude-sonnet-5"`.
- **C2.3** A rendered multi-agent `.paperclip.yaml` carries those ids under
  `agents.<slug>.adapter.config.model`.
- **C2.4** `parse_model_preferences` resolves the `opus`/`sonnet` tier keywords to the
  bundle-facing constants.

## C3 — The split is structural, not nominal

- **C3.1** `renderers/adapter.py` does not import `OPUS_MODEL`, `SONNET_MODEL`,
  `CONTENT_MODEL`, or `STRUCTURAL_MODEL`. Asserted by reading the module source, so it fails if
  a future edit reaches back across the line.
- **C3.2** This assertion fails against the pre-change module. A test that could not fail would
  be recording nothing; the split is only real if crossing it is detectable.

## C4 — Cost estimation

- **C4.1** Every model id in `{CONTENT_MODEL, STRUCTURAL_MODEL}` is a key of
  `TOKEN_PRICES_PER_MTOK`. Derived by iterating the constants — restating the ids as literals
  would pass even if both the constant and the table were wrong in the same direction.
- **C4.2** `estimate_cost` for a model absent from the table still returns the documented
  fall-through (the Sonnet rate), unchanged behaviour.
- **C4.3** `estimate_cost(CONTENT_MODEL, 1e6, 1e6) == 30.0` and
  `estimate_cost(STRUCTURAL_MODEL, 1e6, 1e6) == 18.0` — the standard published rates
  ($5/$25 and $3/$15 per MTok).

## C5 — CLI aliases

- **C5.1** `resolve_model("opus", default=X)` returns `CONTENT_MODEL`;
  `resolve_model("sonnet", default=X)` returns `STRUCTURAL_MODEL`.
- **C5.2** `resolve_model("opus-5", ...)` and `resolve_model("sonnet-5", ...)` resolve likewise.
- **C5.3** `resolve_model("opus-4.8", ...)` returns the string `"opus-4.8"` unchanged — the
  superseded alias resolves to nothing, rather than to a different model than its name says.
- **C5.4** `resolve_model("claude-opus-4-8", ...)` returns it unchanged, so a deliberate
  older-model run is still expressible by full id.
