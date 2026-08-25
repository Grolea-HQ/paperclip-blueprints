# Feature 025 — Current-generation model defaults, and the two jobs one constant was doing

**Status:** Implemented
**Branch:** `025-current-generation-model-defaults`
**ADR:** ADR-045

---

## Context

`OPUS_MODEL` and `SONNET_MODEL` in `config.py` are `claude-opus-4-8` and `claude-sonnet-4-6`.
The current generation is Claude Opus 5 (`claude-opus-5`) and Claude Sonnet 5
(`claude-sonnet-5`). Moving to them is the request.

The request is not a rename, because those two constants answer to **two different
authorities**:

1. **Generation-time.** Through `CONTENT_MODEL` and `STRUCTURAL_MODEL`, they select the model
   *this tool calls*. Validity here is decided by our own API key and by whether the model
   accepts this codebase's request shape — streaming, adaptive thinking, `output_config.effort`,
   `output_config.format`. It is checkable from this repo, with a live call.
2. **Import-time.** Through `renderers/adapter.py`'s role table, the same strings are emitted as
   every generated agent's `adapter.config.model` in `.paperclip.yaml`. Validity here is decided
   by the operator's Paperclip instance and its `claude_local` adapter build. ADR-017 already
   records that the importer does not validate these ids for env-free worker kinds — they are
   *preferences*. It is **not** checkable from this repo.

One pair of constants means one edit moves both, and nothing states they must agree. They
happen to agree today; that agreement is a coincidence of tiering, not a constraint.

## User scenarios

### US1 — The tool generates on the current model generation (P1)

A run calls `claude-opus-5` for content synthesis and `claude-sonnet-5` for structural
transforms.

**Independent test:** the generator unit tests assert the model each call is dispatched with.

### US2 — A generated bundle states a current-generation preference for its agents (P1)

An emitted `.paperclip.yaml` carries `claude-opus-5` for the owner role and `claude-sonnet-5`
for the rest.

**Independent test:** render a multi-agent bundle and read the `adapter.config.model` values.

### US3 — The two jobs cannot be moved by accident again (P1)

Changing what the tool calls does not change what a generated bundle asserts, and vice versa.

**Independent test:** a structural test asserts that the bundle-facing emission path does not
read the generation-time constants. This test **fails before the change** — `adapter.py`
imports `OPUS_MODEL` and `SONNET_MODEL` today — which is what makes it worth having.

### US4 — Cost estimates do not silently misreport (P2)

The price table is keyed on model id and falls through to the Sonnet entry for any unknown key,
so a model rename without a table update changes every estimate with no error raised.

**Independent test:** every model id this tool can call by default has its own entry in
`TOKEN_PRICES_PER_MTOK`, asserted by iterating the constants rather than by restating them.

## Requirements

- **FR-001**: `CONTENT_MODEL` resolves to `claude-opus-5`; `STRUCTURAL_MODEL` to
  `claude-sonnet-5`.
- **FR-002**: The per-agent preference emitted into `.paperclip.yaml` is `claude-opus-5` for the
  `owner` role and `claude-sonnet-5` for `manager`, `engineering`, and `generic`.
- **FR-003**: The bundle-facing model ids are **separate named constants** from the
  generation-time ones, and `renderers/adapter.py` reads only the bundle-facing ones.
- **FR-004**: The brief's `opus`/`sonnet` tier keywords (`parse_model_preferences`) resolve to
  the **bundle-facing** ids — that path also emits into `.paperclip.yaml`.
- **FR-005**: `TOKEN_PRICES_PER_MTOK` carries an entry for every model id the tool calls by
  default, at that model's standard published rate.
- **FR-006**: `--model` aliases name the current generation (`opus-5`, `sonnet-5`, and the bare
  `opus`/`sonnet`). The superseded version-suffixed aliases (`opus-4.8`, `sonnet-4.6`) are
  **removed** rather than repointed: repointing would make `--model opus-4.8` silently select
  Opus 5. Removal lets the value fall through `resolve_model` unchanged as a literal model id,
  so a user who genuinely wants the older model still gets it by full id.
- **FR-007**: Operator-facing text naming the required model access (`SETUP.md`, the `--model`
  help string) names the current ids.

## Success criteria

- **SC-001**: No default code path calls `claude-opus-4-8` or `claude-sonnet-4-6`.
- **SC-002**: A rendered multi-agent `.paperclip.yaml` carries only current-generation model ids.
- **SC-003**: `renderers/adapter.py` imports no generation-time model constant.
- **SC-004**: `estimate_cost` never falls through to the default entry for a model the tool
  calls by default.

## Out of scope

- Whether the cost summary should exist at all. It is required by **SC-011 of spec 002** ("a
  completed generate run prints a total token/cost summary"), which is a settled decision; this
  feature does not reopen it. What this feature does change is that the table now carries the
  date its figures were verified and the price event that was live when they were chosen.
- Verifying that a Paperclip instance's `claude_local` adapter recognises `claude-opus-5`. That
  is operator-environment and unverifiable from this repo (ADR-017); ADR-045 records it as
  unverified rather than as verified-good.
- `CODEX_MODEL`. It is already a bundle-facing-only constant and is untouched.
