---
description: "Task list for feature 014 — per-agent run-policy override from the brief"
---

# Tasks: Per-agent run-policy override from the brief

**Input**: Design documents from `specs/014-run-policy-override/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/run-policy-override.md

**Tests**: REQUIRED. Constitution III mandates test-first (red-green-refactor) for non-trivial logic
(parser, merge, brief validation). Every implementation task is preceded by a failing test task.

**Organization**: Grouped by user story. US1 and US3 are Priority P1; US2 is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1 / US2 / US3, or `Foundation` for shared prerequisites
- All paths are relative to repo root

---

## Phase 1: Setup & Baseline

**Purpose**: Pin "today's" output before any code changes, so the backward-compat gate (US3, T022)
has an honest reference.

- [ ] T001 [Foundation] Capture the pre-change baseline: pick a representative multi-agent fixture
  brief with **no** run-policy values (reuse an existing fixture in `tests/` if one covers ≥1 root +
  ≥1 non-root + a poller-titled agent; otherwise add one). Generate its `.paperclip.yaml` on the
  **current, unmodified** generator and save the exact `runPolicy` blocks as the golden reference
  used by T022. Record it as a committed fixture (e.g. `tests/fixtures/runpolicy_baseline.yaml` or an
  inline constant in the US3 test). MUST be done first, before any source is touched (T003 onward).

**Checkpoint**: baseline recorded; safe to modify source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared model/brief surface every story builds on. All backward-compatible (new fields
default to absent).

- [ ] T002 [P] [Foundation] Failing test: `RunPolicy` accepts optional `heartbeat_enabled` (default
  `None`); a two-arg `RunPolicy(max_turns_per_run=.., max_concurrent_runs=..)` still constructs and
  has `heartbeat_enabled is None`. `tests/test_run_policy.py`
- [ ] T003 [Foundation] Add `heartbeat_enabled: bool | None = None` to the `RunPolicy` dataclass.
  `src/paperclip_blueprints/renderers/run_policy.py` (depends on T002)
- [ ] T004 [P] [Foundation] Failing test: `RunPolicyOverride` frozen dataclass with three optional
  fields, all defaulting to `None`. `tests/test_run_policy.py`
- [ ] T005 [Foundation] Add the `RunPolicyOverride` dataclass. `renderers/run_policy.py` (T004)
- [ ] T006 [P] [Foundation] Failing test: `parse_brief` reads a new "Run-policy overrides" section
  into `CompanyBrief.run_policy_preferences: list[str] | None`; absent/blank section ⇒ `None`; a
  brief with no such section is unchanged in every other field. `tests/test_models.py`
- [ ] T007 [Foundation] Add `run_policy_preferences: list[str] | None = None` to `CompanyBrief` and
  parse the new section. `src/paperclip_blueprints/models/input.py` (T006)
- [ ] T008 [P] [Foundation] Failing test: syntactic validation (FR-010) raises `BriefValidationError`
  for — non-positive / non-integer turns or concurrency; unknown clause keyword; unknown heartbeat
  token; a line with no clause; the **same reference** given conflicting values for one field. All
  problems reported together. `tests/test_models.py`
- [ ] T009 [Foundation] Implement the syntactic validation in brief parsing/validation.
  `models/input.py` (T008). No agent knowledge here — value/shape checks only.

**Checkpoint**: model + brief foundation ready; stories can proceed.

---

## Phase 3: User Story 1 — Bound turns/concurrency for a named agent (Priority: P1) 🎯 MVP

**Goal**: A brief line naming an agent with `max turns` / `max concurrent` puts those exact values
on that agent in `.paperclip.yaml`, overriding the role-derived value per field; other agents
unchanged; an unmatched reference warns and is skipped.

**Independent Test**: Generate from a brief overriding one agent's turns+concurrency; assert that
agent's emitted values equal the stated values and every other agent equals a no-override run.

- [ ] T010 [P] [US1] Failing test: `parse_run_policy_preferences(lines, agents)` maps turns/
  concurrency clauses to per-slug `RunPolicyOverride`; boundary-safe reference matching (a line for
  `analyst` does not match `senior-analyst`); a reference matching several agents fans out; returns
  `unmatched` for a reference hitting no agent; `(None, agents) → ({}, [])`. `tests/test_run_policy.py`
- [ ] T011 [US1] Implement `parse_run_policy_preferences`, reusing `adapter._matched_ref` /
  `_boundary_contains`. `renderers/run_policy.py` (T010). Assumes lines already syntactically valid.
- [ ] T012 [P] [US1] Failing test: `assign_run_policies(agents, overrides)` overlays each **set**
  override field onto the ADR-027 role base; an unset field keeps the base; overriding one agent
  leaves all others identical to `assign_run_policies(agents)`. `tests/test_run_policy.py`
- [ ] T013 [US1] Add optional `overrides` param to `assign_run_policies` and apply the per-field
  overlay. `renderers/run_policy.py` (T012). Default `None` ⇒ identical to today (guards T022).
- [ ] T014 [US1] Wire `render.py`: parse `brief.run_policy_preferences`, pass overrides into
  `assign_run_policies`, and surface each unmatched reference via the `warn` sink (message per the
  contract), mirroring the adapter unmatched-preference warning. `renderers/render.py` (T011, T013)
- [ ] T015 [P] [US1] Failing test at the render path: a brief overriding one agent's turns+
  concurrency emits those values under that agent's `runPolicy`; other agents unchanged; an
  unmatched-reference line raises a warning through `warn`. `tests/test_render.py` (T014)

**Checkpoint**: US1 fully functional and independently testable.

---

## Phase 4: User Story 2 — Disable heartbeat for a named agent (Priority: P2)

**Goal**: A brief line setting `heartbeat off`/`on` for an agent emits `runPolicy.heartbeatEnabled`
for that agent only; nothing is emitted for any agent the operator doesn't mention.

**Independent Test**: Generate from a brief setting heartbeat off for one agent; assert
`heartbeatEnabled: false` appears for it and for no other agent; a brief mentioning no heartbeat
emits the key nowhere.

- [ ] T016 [P] [US2] Failing test: `parse_run_policy_preferences` recognizes heartbeat tokens
  (`on`/`enabled`/`true`, `off`/`disabled`/`false`) → `override.heartbeat_enabled`, and
  `assign_run_policies` carries it onto the resolved `RunPolicy`; it stays `None` for unmentioned
  agents. `tests/test_run_policy.py`
- [ ] T017 [US2] Extend the parser (heartbeat clause recognition) and the merge to carry
  `heartbeat_enabled`. `renderers/run_policy.py` (T016)
- [ ] T018 [P] [US2] Failing test: `paperclip_yaml.j2` emits `heartbeatEnabled: <true|false>`
  (lower-cased) **only** when `heartbeat_enabled is not None`, and omits the key entirely when
  `None`. `tests/test_render.py`
- [ ] T019 [US2] Add the conditional `heartbeatEnabled` line to the `runPolicy` block.
  `src/paperclip_blueprints/templates/paperclip_yaml.j2` (T018)
- [ ] T020 [P] [US2] Failing test: `schema_shape` validator accepts a boolean `heartbeatEnabled` and
  fails a non-boolean, blocking the write (Constitution II). `tests/test_validators.py`
- [ ] T021 [US2] Extend the schema-shape validator to assert `runPolicy.heartbeatEnabled`, when
  present, is boolean. `src/paperclip_blueprints/validators/schema_shape.py` (T020)

**Checkpoint**: US2 functional; US1 + US2 both work independently.

---

## Phase 5: User Story 3 — A brief with no run-policy values changes nothing (Priority: P1)

**Goal**: The backward-compat guarantee, held as its **own** explicitly-tested gate — the one most
likely to erode quietly once overrides and the heartbeat tri-state exist.

**Independent Test**: Diff a no-override generation against the T001 baseline — zero diff.

- [ ] T022 [US3] **Backward-compat gate (standalone — do NOT fold into any other assertion).**
  Failing-then-passing test: generating from a brief with **no** `run_policy_preferences` produces a
  `.paperclip.yaml` **byte-identical** to the T001 baseline. The test MUST assert both:
  (a) every agent's `maxTurnsPerRun` / `maxConcurrentRuns` equals the baseline (role rule untouched);
  (b) **no `heartbeatEnabled` key appears for any agent** — the tri-state `None` renders nothing.
  Give it its own test function whose name states the guarantee (e.g.
  `test_no_run_policy_prefs_is_byte_identical_to_baseline`). `tests/test_run_policy_backcompat.py`
  (depends on US1 + US2 complete so the tri-state template path exists to be exercised)
- [ ] T023 [US3] Run the full existing suite and confirm zero behavioral drift for bundles that
  state no run-policy values (existing render/bundle/golden tests still green). `uv run pytest -q`

**Checkpoint**: the erosion-guard gate is locked; all three stories independently pass.

---

## Phase 6: Polish, Docs & Gates

- [ ] T024 [P] Add the "Run-policy overrides (optional)" section to `examples/input-template.md`
  (FR-013) using the text in `contracts/run-policy-override.md` §6 — three values, optional, names
  agents, blank ⇒ unchanged. Keep the section number consistent with the existing template ordering.
- [ ] T025 [P] Walk through `quickstart.md` end-to-end (operator path): write an override, generate,
  see it in `.paperclip.yaml`; blank section ⇒ no change. Fix any drift between doc and behavior.
- [ ] T026 Final gates: `uv run ruff check .` **and** `uv run ruff format --check .` **and**
  `uv run pyright` all clean (ruff format is an explicit end-session gate, not just ruff check).

---

## Dependencies & Execution Order

### Phase order
- **T001 (baseline) MUST be first** — it captures unmodified output; any earlier source edit
  corrupts the reference.
- **Phase 2 (Foundational)** blocks all stories.
- **US1 (Phase 3)** and **US2 (Phase 4)** depend only on Foundational. They edit the same
  `run_policy.py` parser/merge, so if worked concurrently, serialize T011/T013 against T017.
- **US3 (Phase 5, T022)** depends on US1 **and** US2 — the byte-identical test must exercise the
  tri-state template path. This is the standalone backward-compat gate.
- **Phase 6** depends on all stories complete.

### Within each story
- Test task (failing) precedes its implementation task — always.
- Parser (T011) before the merge wiring uses it; merge (T013) before render wiring (T014); render
  wiring before the render-path test passes (T015).

### Parallel opportunities
- T002 / T004 / T006 / T008 (Foundational tests, different concerns) can be written in parallel.
- Across stories: US1 and US2 test-writing can start together once Foundational is green.
- T024 / T025 (docs) run in parallel at the end.

## Notes

- Task IDs are sequential T001–T026 with no gaps; US3's standalone backward-compat gate is T022.
- Keep the feature a **pure carrier**: no defaults, no heuristics, no inference of values from role
  or company shape (FR-007). The parser reads only stated tokens.
- Commit is the operator's call — do not auto-commit between tasks.
- The single highest-value invariant is T022: a silent regression there re-prices every existing
  operator's bundle. Treat a failure of T022 as release-blocking.
