# Implementation Plan: Per-agent run-policy override from the brief

**Branch**: `014-run-policy-override` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/014-run-policy-override/spec.md`

## Summary

Let the operator's brief state per-agent run-policy values — a maximum-turns-per-run cap, a
maximum-concurrent-runs limit, and a heartbeat on/off toggle — and carry those exact values into
the bundle's `.paperclip.yaml` `runPolicy` block so the deployer applies them. The feature layers
a **pure, deterministic override** on top of the existing role-derived run policy (ADR-027): a
brief-stated value substitutes for the role-derived value for that agent and field; the role rule
is the untouched base. The heartbeat toggle is a new, brief-only field emitted only when stated.
No new defaults, heuristics, or inference — the module transports operator-stated values and
nothing else. Structure mirrors the two established per-agent brief-driven derivations: budget
(ADR-012, `renderers/budget.py`) and model preferences (ADR-017, `renderers/adapter.py`,
`parse_model_preferences`). Emit/carrier side only; the deployer consumer lives in the private
repo and is out of scope.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Pydantic v2 (brief model + validation), Jinja2 (`paperclip_yaml.j2`
carrier), ruamel.yaml (round-trip). No new dependency — the feature is pure Python over existing
libraries.

**Storage**: N/A (in-memory generation → files on disk).

**Testing**: pytest, test-first per Constitution III. New `tests/test_run_policy.py` cases (the
file exists) plus brief-parsing cases in `tests/test_models.py` and a render-path assertion.

**Target Platform**: CLI tool (local generation).

**Project Type**: Single project (library + Typer CLI).

**Performance Goals**: N/A — deterministic, no I/O, no model call; negligible cost.

**Constraints**: Pure and deterministic (no LLM, no I/O); byte-identical output when the brief
states nothing (backward-compat gate); generated `.paperclip.yaml` stays schema-valid
(Constitution II).

**Scale/Scope**: A single company bundle (typically 8–16 agents). One new brief field, one new
input-template section, additions to one renderer module, one template block, and validation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Spec-Driven Development First** — PASS. `/speckit.specify` → this plan → `/speckit.tasks` →
  `/speckit.implement`, in order. Spec is settled and validated.
- **II. Schema-Valid Bundles (NON-NEGOTIABLE)** — PASS with a named check. The new
  `runPolicy.heartbeatEnabled` key is additive under a block the validators already tolerate
  (ADR-027 renders `runPolicy` today; `test_run_policy.py` and the schema-shape/integrity
  validators are green). The plan requires the bundle validators to stay green with the new key,
  and adds a validator assertion so a malformed emission cannot reach disk.
- **III. Test-First for Non-Trivial Logic** — PASS. The line parser, the override merge, and the
  brief-field validation are non-trivial and MUST be built red-green-refactor. Pure-templating glue
  (the one `{% if %}` in the Jinja block) is exempt.
- **IV. Brief-Faithful Generation Over Recycled Shape** — PASS, and strongly reinforced. The
  feature is pure passthrough of operator-stated values with an explicit no-inference rule
  (FR-007); no model creativity is involved. This is the "structural rule the tool enforces, not a
  model preference" principle applied to run-policy values.
- **V. Phased Scope & YAGNI** — PASS. This is v0.1b carrier work (the bundle the operator imports).
  The deployer that consumes `runPolicy` is v0.2 / private-repo scope and is explicitly excluded
  (FR-012). No deployment automation is added here.

No violations → Complexity Tracking table omitted.

## Project Structure

### Documentation (this feature)

```text
specs/014-run-policy-override/
├── plan.md              # This file
├── research.md          # Phase 0 output — grammar & layering decisions
├── data-model.md        # Phase 1 output — entities & validation rules
├── quickstart.md        # Phase 1 output — operator + developer walkthrough
├── contracts/
│   └── run-policy-override.md   # Module interface, brief field, YAML carrier, template section
├── checklists/
│   └── requirements.md  # From /speckit.specify
└── tasks.md             # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/paperclip_blueprints/
├── models/
│   └── input.py                 # CHANGE: add `run_policy_preferences: list[str] | None`;
│                                #         parse a new input-template section; syntactic
│                                #         validation of stated values (FR-010)
├── renderers/
│   ├── run_policy.py            # CHANGE: add `heartbeat_enabled` to RunPolicy; add
│   │                            #         `parse_run_policy_preferences(...)`; add an
│   │                            #         override-merge over the role-derived base
│   ├── adapter.py               # REUSE (import only): boundary-safe matching helpers
│   │                            #         (`_matched_ref`, `_boundary_contains`)
│   └── render.py                # CHANGE: parse brief overrides, merge onto role base,
│                                #         surface unmatched-reference warnings via `warn`
├── templates/
│   └── paperclip_yaml.j2        # CHANGE: emit `heartbeatEnabled` under runPolicy when present
└── validators/
    └── schema_shape.py          # VERIFY/EXTEND: runPolicy block (incl. heartbeatEnabled) shape

examples/
└── input-template.md            # CHANGE: new "Run-policy overrides (optional)" section (FR-013)

tests/
├── test_run_policy.py           # EXTEND: parser, merge, heartbeat-only-when-stated, no-op
├── test_models.py               # EXTEND: brief field parsing + malformed-value rejection
└── test_render.py / test_bundle.py  # EXTEND: byte-identical no-op; emitted values; warnings

docs/adr/
└── 034-brief-run-policy-override.md   # NEW ADR (number 034 per operator instruction)
```

**Structure Decision**: Single-project layout, extending the existing per-agent-derivation seam.
The feature slots into the exact three places budget and adapter preferences already occupy: a
brief field + parser (`models/input.py`), a pure renderer (`renderers/run_policy.py`), and the
`.paperclip.yaml` carrier (`render.py` context + `paperclip_yaml.j2`). No new module directory, no
new dependency, no new top-level structure.

## Phase 0 — Research

See [research.md](./research.md). Resolves: the brief line grammar (colon-delimited
reference + typed clauses), where malformed-value validation lives (syntactic → brief validation;
semantic match → render-time warning), the heartbeat carrier key (`runPolicy.heartbeatEnabled`),
and the layering mechanics over ADR-027 (field-level override, base untouched).

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md) — the `RunPolicyOverride` entity, the extended `RunPolicy`, the
  new brief field, and all validation rules mapped to FRs.
- [contracts/run-policy-override.md](./contracts/run-policy-override.md) — the module function
  signatures, the brief-section grammar, the `.paperclip.yaml` `runPolicy` fragment, and the
  input-template section text.
- [quickstart.md](./quickstart.md) — an operator walkthrough (write an override, see it in the
  bundle) and a developer walkthrough (run the tests).

**Agent context update**: SKIPPED. CLAUDE.md contains no `<!-- SPECKIT START/END -->` markers, and
the operator rule forbids modifying CLAUDE.md without an ADR. The "Active feature plan" pointer is
left as the operator's to move.

**Decision record**: `docs/adr/034-brief-run-policy-override.md` is authored in this phase (the
layering-over-ADR-027 decision + the new brief channel). Numbered 034 per operator instruction (028
is skipped here).
