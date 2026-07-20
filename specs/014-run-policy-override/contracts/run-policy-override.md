# Contract: Per-agent run-policy override from the brief

This is a library + CLI tool; the "interfaces" are the module function signatures, the brief input
grammar, the emitted `.paperclip.yaml` fragment, and the input-template section.

## 1. Module interface — `renderers/run_policy.py`

```python
@dataclass(frozen=True)
class RunPolicy:
    max_turns_per_run: int
    max_concurrent_runs: int
    heartbeat_enabled: bool | None = None      # NEW: None => not stated => not emitted


@dataclass(frozen=True)
class RunPolicyOverride:
    max_turns_per_run: int | None = None
    max_concurrent_runs: int | None = None
    heartbeat_enabled: bool | None = None


def parse_run_policy_preferences(
    preferences: Sequence[str] | None,
    agents: Sequence[_AgentRef],
) -> tuple[dict[str, RunPolicyOverride], list[str]]:
    """Resolve brief run-policy override lines to per-slug overrides.

    Returns (overrides, unmatched):
      - overrides: agent slug -> RunPolicyOverride (only agents an override matched)
      - unmatched: override lines whose reference matched no agent (caller warns)
    Boundary-safe reference matching reuses adapter._matched_ref / _boundary_contains.
    Assumes lines are already syntactically valid (validated at brief-parse time).
    """


def assign_run_policies(
    agents: list[AgentDefinition],
    overrides: dict[str, RunPolicyOverride] | None = None,   # NEW optional param
) -> dict[str, RunPolicy]:
    """Role-derived base (ADR-027) with per-agent, per-field brief overrides applied.

    overrides is None/empty => identical to today's output (backward compat).
    Field overlay: a set override field replaces the base; unset fields keep the base.
    heartbeat_enabled has no base — it is None unless an override sets it.
    """
```

**Contract guarantees**
- `assign_run_policies(agents)` (no `overrides`) returns exactly today's result — same call sites,
  same values. (SC-002 / FR-006)
- `parse_run_policy_preferences(None, agents) == ({}, [])`.
- Pure/deterministic: no I/O, no model call; output depends only on inputs. (FR-008)
- No field is ever populated from role/risk/shape — only from a stated override. (FR-007)

## 2. Brief input grammar (new input-template section)

One override per line:

```
<agent reference>: <clause>[, <clause>]...
```

Clauses (case-insensitive; hyphen or space tolerated):

| Concern | Keyword (aliases) | Value |
|---|---|---|
| Turns cap | `max turns` (`turns`, `max-turns`) | positive integer |
| Concurrency limit | `max concurrent` (`concurrent`, `max-concurrent`, `concurrency`) | positive integer |
| Heartbeat | `heartbeat` | `on`/`enabled`/`true` or `off`/`disabled`/`false` |

Examples:

```
research-analyst: max turns 8, heartbeat off
CEO: max concurrent 1
All watchers: max turns 5
```

- Reference = text left of the first `:`; matched boundary-safe to slug / title / name.
- A line must contain ≥1 clause.
- Rejected at brief-validation time: non-positive/non-integer value, unknown clause keyword,
  unknown heartbeat state, same reference with conflicting values for one field. (FR-010)

## 3. Emitted `.paperclip.yaml` fragment (`templates/paperclip_yaml.j2`)

```yaml
agents:
  research-analyst:
    runPolicy:
      maxTurnsPerRun: 8          # brief override (base would be role-derived)
      maxConcurrentRuns: 2       # role-derived base (unstated by brief)
      heartbeatEnabled: false    # brief-stated only; omitted when unstated
```

Template change (additive, inside the existing `runPolicy` block):

```jinja
    runPolicy:
      maxTurnsPerRun: {{ run_policies[a.slug].max_turns_per_run }}
      maxConcurrentRuns: {{ run_policies[a.slug].max_concurrent_runs }}
{% if run_policies[a.slug].heartbeat_enabled is not none %}
      heartbeatEnabled: {{ run_policies[a.slug].heartbeat_enabled | lower }}
{% endif %}
```

**Guarantee**: when no agent has a stated heartbeat and no override changes turns/concurrency, the
rendered block is byte-identical to today's. (SC-002)

## 4. Validator contract (`validators/schema_shape.py`)

- `runPolicy.heartbeatEnabled`, when present, MUST be a boolean; a non-boolean is a schema-shape
  failure that blocks the write. (Constitution II)
- No change to the existing `maxTurnsPerRun` / `maxConcurrentRuns` assertions.

## 5. Warning contract (`renderers/render.py`, via `warn` sink)

- Unmatched reference: `run-policy override <line> names no agent — no run policy is set for it`
  (advisory; generation proceeds). Mirrors the adapter unmatched-preference warning. (FR-009)
- Cross-reference collision on one agent+field: resolved **deterministically last-in-line-order
  with no warning**. Two distinct references legitimately overlapping on one agent — a broad
  default plus a specific exception (e.g. `All watchers: max turns 5` then
  `lead-watcher: max turns 12`) — is a **supported, intentional pattern**, so a collision warning
  would fire on correct usage. The later line wins per field; determinism holds (FR-008). See
  ADR-034 (recorded as a deliberate deviation from this contract's original draft, which specified
  an advisory warning here). (D4)

## 6. Input-template section text (added to `examples/input-template.md`, FR-013)

> ## N. Run-policy overrides (optional)
>
> By default the tool sets each agent's per-run turn cap and concurrent-run limit by role. If you
> want a specific agent bounded differently — or run only on demand, never on a heartbeat — state it
> here. Leave this blank to keep the defaults; an empty section changes nothing.
>
> One override per line, naming the agent and the values:
>
> - `<agent>: max turns <N>` — cap turns per wake (guards against a run that loops and burns budget)
> - `<agent>: max concurrent <N>` — cap simultaneous runs of that agent
> - `<agent>: heartbeat off` — do not wake this agent on a heartbeat (on/off)
>
> Combine on one line: `research-analyst: max turns 8, heartbeat off`
>
> **Your overrides:**
>
> - [e.g., "CEO: max concurrent 1"]
