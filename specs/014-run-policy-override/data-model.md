# Phase 1 Data Model: Per-agent run-policy override from the brief

## Entities

### RunPolicyOverride (new)

An operator-stated, per-agent set of optional run-policy values, parsed from one brief line. All
fields optional; at least one is set (a line with no clause is a syntactic error).

| Field | Type | Notes |
|---|---|---|
| `max_turns_per_run` | `int \| None` | Positive integer when set; `None` = not stated. |
| `max_concurrent_runs` | `int \| None` | Positive integer when set; `None` = not stated. |
| `heartbeat_enabled` | `bool \| None` | `None` = not stated (nothing emitted); `True`/`False` = explicit toggle. |

Represented as a frozen dataclass in `renderers/run_policy.py` (a transport value, not a persisted
model — mirrors `AdapterChoice`). It is keyed by resolved agent slug in the override map.

### RunPolicy (extended)

The existing ADR-027 result, plus one new field.

| Field | Type | Source |
|---|---|---|
| `max_turns_per_run` | `int` | Role-derived base (ADR-027), or brief override. Always present. |
| `max_concurrent_runs` | `int` | Role-derived base (ADR-027), or brief override. Always present. |
| `heartbeat_enabled` | `bool \| None` (**new**, default `None`) | Brief-only. `None` renders nothing. |

Backward-compat: the new field defaults to `None`, so a `RunPolicy` built without it (all existing
call sites and tests) is unchanged and renders exactly today's two-key block.

### CompanyBrief (extended)

One new optional field on the existing Pydantic model in `models/input.py`.

| Field | Type | Notes |
|---|---|---|
| `run_policy_preferences` | `list[str] \| None = None` | Raw override lines from the new input-template section. `None`/empty ⇒ feature dormant. Mirrors `adapter_preferences`. |

## Derivation flow

```
brief.run_policy_preferences (raw lines)
        │  parse_run_policy_preferences(lines, agents)      [renderers/run_policy.py]
        ▼
(overrides: dict[slug -> RunPolicyOverride], unmatched: list[str])
        │  merge over assign_run_policies(agents)  (role-derived base, ADR-027)
        ▼
run_policies: dict[slug -> RunPolicy]   → template context "run_policies" (render.py)
        │  paperclip_yaml.j2 runPolicy block
        ▼
.paperclip.yaml  (maxTurnsPerRun, maxConcurrentRuns, [heartbeatEnabled])
```

`unmatched` → `warn(...)` in `render.py` (advisory, non-blocking).

## Validation rules (mapped to FRs)

Syntactic (at `parse_brief` / `CompanyBrief` validation → `BriefValidationError`, no agents needed):

| Rule | FR | Message intent |
|---|---|---|
| A turns / concurrency value is a positive integer | FR-010 | name the line + the offending value |
| Clause keyword is recognized (turns / concurrent / heartbeat + aliases) | FR-010 | name the unrecognized token |
| Heartbeat state is a recognized on/off token | FR-010 | name the unrecognized state |
| A line has at least one clause | FR-010 | "run-policy override states no value" |
| The **same reference** is not given conflicting values for one field | FR-010 | name the reference + field |

Semantic (at render time → `warn`, non-blocking):

| Rule | FR | Behavior |
|---|---|---|
| Reference matches ≥1 generated agent | FR-009 | no match ⇒ warn, emit nothing for it |
| Two distinct references collide on one agent+field with conflicting values | edge (D4) | warn, last-in-line-order wins (deterministic) |

Invariants:

- **No-op identity** (FR-006, SC-002): `run_policy_preferences` empty/`None` ⇒ `overrides` empty ⇒
  `run_policies` equals `assign_run_policies(agents)` exactly ⇒ byte-identical `.paperclip.yaml`.
- **Field independence** (FR-004): overriding one field never mutates another.
- **Heartbeat-only-when-stated** (FR-005, SC-004): `heartbeat_enabled is None` ⇒ key absent.
- **No inference** (FR-007): the parser reads only stated tokens; it never fills a value from role,
  risk, or company shape.
- **Determinism** (FR-008): pure function of `(lines, agents)`; brief-line order is the only tie-break.
