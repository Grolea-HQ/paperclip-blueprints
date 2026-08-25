# ADR-017: Per-agent model preference in the bundle — (adapter type + model id), no env

## Status

Accepted

## Date

2026-06-20

## Context

`.paperclip.yaml` today emits only `role` and `budgetMonthlyCents` per agent. The
operator must set each agent's model by hand after import. Shipping a sensible
per-agent model preference in the bundle makes the generated company more
ready-to-run, and is a parity gap with comparable bootstrappers. ADR-015 already
ruled the per-agent **model id** to be on the portable side of the boundary.

Verifying the mechanics against the platform (v2026.618.0 importer + adapter
registry) surfaced a refinement that ADR-015 did not yet capture:

- A per-agent model rides at `agents.<slug>.adapter.config.model` — **nested under
  an `adapter` with a `type`.** There is no bare per-agent model field.
- The importer **requires a registered adapter type**: when `adapter.type` is
  absent it defaults to `"process"`, which is **not** in the adapter registry, so
  the apply phase rejects it (`Unknown adapter type`). A model id therefore cannot
  ride alone — it needs a registered adapter `type` as its carrier.
- Verified env-free at import: `claude_local` (injects no env) and `codex_local`
  (only appends a `--skip-git-repo-check` arg). `opencode_local` requires a valid
  model id **and** Manifest/provider routing (env), so it is excluded.
- Model ids are **per-instance and dynamic** (each adapter lists/refreshes models
  from its provider, with a fallback list). For the env-free types we use, the
  importer does **not** validate the model id (only `opencode_local` does). So an
  emitted model id is a **preference**; whether a given instance actually serves it
  is **availability** — the operator's environment, not the bundle's.

This mirrors ADR-015's model-preference-vs-availability nuance one level up: the
**adapter `type` + model id** is the portable preference; the adapter's **`env`**
(provider routing, base URLs, credentials) and whether the instance has that
adapter configured with working credentials are the **operator-environment**.

## Decision

Emit a per-agent **portable model preference** in `.paperclip.yaml`:

```yaml
agents:
  ceo:
    role: ceo
    adapter:
      type: claude_local
      config:
        model: claude-opus-4-8
    budgetMonthlyCents: 5540
```

1. **Carrier = (adapter type + model id), nothing else under `adapter`.** Emit
   `adapter.type` (a registered standard worker kind) and `adapter.config.model`.
   **Never emit `adapter.config.env`** — provider routing, base URLs, and
   credentials stay operator-environment, below the ADR-015 line.

2. **Role-derived defaults, reusing the existing role bucket.** Map each agent's
   `_role_bucket` (the same classifier budgets use) to a (type, model):

   > **Superseded in part by ADR-045 (2026-08-24).** The tiering and the adapter types below
   > are unchanged, but the model ids are now `claude-opus-5` / `claude-sonnet-5`, and they come
   > from their own bundle-facing constants (`AGENT_TOP_TIER_MODEL` / `AGENT_BALANCED_MODEL`)
   > rather than from `OPUS_MODEL` / `SONNET_MODEL` — which select what *this tool* calls and
   > answer to a different authority.

   | Role bucket | adapter type | model id |
   |---|---|---|
   | owner (CEO) | `claude_local` | `claude-opus-4-8` |
   | manager | `claude_local` | `claude-sonnet-4-6` |
   | engineering | `claude_local` | `claude-sonnet-4-6` |
   | generic | `claude_local` | `claude-sonnet-4-6` |

   **`claude_local` is the default for every role** — a generated company runs
   out-of-the-box on a single provider. The owner/CEO gets the top tier (it reasons
   over the whole company); every other role gets the balanced tier (Sonnet, which
   is also strong at code, so engineering shares it for cost-consistency); Opus is
   reserved for the owner. Model ids are the project's existing Claude constants
   (Opus is `OPUS_MODEL`, currently `claude-opus-4-8`); they are **preferences**,
   adjustable by the operator, and not import-validated for these types.

   **`codex_local` is a fully supported alternative worker, not the default.** It
   stays in `PORTABLE_ADAPTER_TYPES` and the S12 allowlist, and the `CODEX_MODEL`
   constant (`gpt-5.3-codex`) and the `_BY_ROLE` structure are kept, so an operator
   opts a role into Codex by swapping its per-agent `(type, model)` preference — a
   one-line change, env-free and import-validated. (No CLI flag or brief field to
   choose the adapter yet — YAGNI; operator-selectable adapters would be their own
   small spec.) `opencode_local`/`hermes_local` and Manifest routing remain v0.2
   deployer territory (they need env).

3. **Boundary refinement (refines ADR-015).** The portable unit is the
   **(adapter type + model id)** preference; the operator-environment exclusion is
   **`adapter.config.env`** (and the instance's actual adapter/credential/model
   availability). Adapter type is the portable carrier — the minimal thing that
   makes the model id take effect — exactly the same shape as model preference vs
   model availability. ADR-015's "rides the bundle: per-agent model id" line is
   read as this (type + model) pair; `env` is the named exclusion.

4. **Importability is a hard gate (Constitution II).** A validator asserts every
   emitted `adapter.type` is in the allowed env-free set and that **no agent emits
   `adapter.config.env`**. Built test-first. A clean live import of a
   `type`+`model`, no-`env` agent into a v2026.618.0 instance is the acceptance
   check (run alongside the other live-618 checks). If a chosen adapter type turns
   out to require `env` at import (so type+model-without-env breaks import), **stop
   and report — do not emit `env` to compensate.**

5. **Deferred (out of scope for v0.1).** ~~Parsing the free-text
   `input.adapter_preferences` into structured per-role overrides~~ — the per-role **model
   tier** part is **now honored in v0.1** (see the 2026-07-01 amendment below); `opencode_local`
   + Manifest routing and adapter-**type** overrides (`codex_local`/`hermes_local` per role)
   remain deferred — they need instance/env knowledge and stay with the v0.2 deployer
   (`adapter_assigner.py`).

## Consequences

### Positive
- Generated companies ship a sensible per-agent model out of the box; less manual
  post-import wiring.
- Stays strictly within ADR-015: the bundle carries the portable preference; env,
  routing, credentials, and availability remain operator-side.
- Reuses the existing `_role_bucket` classifier (no new model/field); the model-id
  strings live as named constants in `config.py`, versioned and adjustable.

### Negative / limitations
- Model ids drift over time and per instance; they are best-effort current defaults
  that the operator may adjust (and that the importer does not validate for the
  types we use).
- The role→adapter mapping is coarse (four buckets); richer per-role assignment and
  `adapter_preferences` overrides are deferred.

### Neutral
- Adapter `type` is restricted to a curated env-free allowlist; expanding it (e.g.
  to `opencode_local`) is a future decision gated on the env question.

## Alternatives considered

- **Bare `adapter.config.model`, no type.** Rejected — defaults to the unregistered
  `"process"` adapter and breaks import (Constitution II); a model id cannot ride
  without a registered carrier type.
- **Emit `adapter.config.env` defaults too.** Rejected — provider routing/base
  URLs/credentials are environment-specific (ADR-015 exclusion); baking them breaks
  portability and risks leaking or mismatching config.
- **Use `opencode_local` + Manifest for generic/high-volume roles (full P-PAT-7).**
  Rejected for v0.1 — it requires model validation and Manifest/provider routing
  (env); it stays v0.2 deployer territory.
- **Add a per-agent model field to `AgentDefinition`.** Rejected (YAGNI) — the
  assignment is a render-time derivation from the role bucket, like budgets; no
  model change.

## Amendment — 2026-07-01: per-role model preferences honored (was deferred)

The coarse four-bucket role→model default (owner→Opus, every other role→Sonnet) silently
ignored the brief's explicit per-role model preferences (section 10 `adapter_preferences`), so a
brief that requested e.g. `Senior Analyst → Opus-tier` shipped `claude-sonnet-4-6` in
`.paperclip.yaml` — output that contradicted the brief. Fixed in v0.1: `renderers/adapter.py`
`parse_model_preferences` resolves each `adapter_preferences` line that names a Claude **tier**
(`opus`→`OPUS_MODEL`, `sonnet`→`SONNET_MODEL`) to the agent(s) it references (boundary-safe
slug / title-slug / name-slug, most-specific match), and `assign_adapters` applies it as a
per-slug **model** override — the adapter **type** stays the env-free, import-safe default, so
the no-`env` / type-allowlist rules (Decision §1, S12) are unchanged. Unspecified roles keep the
coarse default; a tier line matching no agent is surfaced through the render `warn` sink.

Adapter-**type** preferences (`codex_local`/`hermes_local`/`opencode_local`, Manifest routing)
remain deferred to the v0.2 deployer (they need instance/env knowledge). This amendment removes
only the **model-tier** part from Decision §5's deferred list.

## References

- ADR-015 (portability boundary — this refines its model-preference-vs-availability
  nuance), ADR-012 (per-agent budgets — same render-derived-from-role-bucket shape),
  ADR-007 (source-of-truth hierarchy)
- Internal P-PAT-7 (role→adapter assignment intent)
- Verified against `paperclipai/paperclip` v2026.618.0: `company-portability.ts`
  (adapter parse/apply, `applyImportAdapterRunDefaults`), `adapters/registry.ts`
  (registered types), `packages/adapters/codex-local` (`DEFAULT_CODEX_LOCAL_MODEL =
  gpt-5.3-codex`)
- Issue #4
