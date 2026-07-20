# Quickstart: Per-agent run-policy override from the brief

## For the operator

1. In your filled-in brief (from `examples/input-template.md`), find the optional **Run-policy
   overrides** section.
2. Add one line per agent you want to bound. You can set any subset of three things:
   - `max turns <N>` — a per-wake turn cap (stops an agent that loops)
   - `max concurrent <N>` — a limit on simultaneous runs of that agent
   - `heartbeat off` — never wake this agent on a heartbeat (it runs only when given work)

   ```
   research-analyst: max turns 8, heartbeat off
   CEO: max concurrent 1
   ```

3. Generate the bundle as usual. In `.paperclip.yaml`, the named agents now carry your values under
   `runPolicy`:

   ```yaml
   research-analyst:
     runPolicy:
       maxTurnsPerRun: 8
       maxConcurrentRuns: 2       # unchanged role default (you didn't set it)
       heartbeatEnabled: false
   ```

4. **Leave the section blank and nothing changes** — every agent keeps the values the tool sets by
   role today. This feature only adds values you explicitly write.

**Notes**
- Name an agent the same way you name it in adapter preferences — by role, title, or slug; matching
  is boundary-safe (`analyst` won't match `senior-analyst`).
- A name that matches no agent produces a warning (not an error) and is skipped.
- A bad value (e.g. `max turns 0`, or `heartbeat maybe`) is rejected up front with a clear message,
  before any generation runs.

## For the developer

The feature follows the per-agent budget / model-preference precedent: a pure, deterministic
renderer driven by the brief, no model call.

- Brief field: `CompanyBrief.run_policy_preferences: list[str] | None` (`models/input.py`), parsed
  from the new input-template section; malformed values rejected in brief validation.
- Parse + match: `parse_run_policy_preferences(lines, agents)` (`renderers/run_policy.py`) reusing
  `adapter.py`'s boundary-safe matcher.
- Merge: `assign_run_policies(agents, overrides)` overlays stated fields onto the ADR-027 role base.
- Carrier: `render.py` puts the merged map in the template context; `paperclip_yaml.j2` emits
  `heartbeatEnabled` only when set.

Run the checks:

```bash
uv run pytest tests/test_run_policy.py tests/test_models.py -q
uv run pytest -q            # full suite — includes the byte-identical no-op assertion
uv run ruff check . && uv run ruff format --check . && uv run pyright
```

Backward-compat gate: a brief with no `run_policy_preferences` must produce a `.paperclip.yaml`
identical to current `main` for the same brief (the no-op test asserts this).
