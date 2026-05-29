# ADR-005 — Phase Split: v0.1a / v0.1b

**Status:** Accepted
**Date:** Pre-v0.1, during the rework
**Relates to:** ADR-002 (output bundle format), ADR-004 (prompt architecture)

---

## Context

The original project skeleton estimated v0.1 at 8-16 hours of focused work. With the corrected output bundle format (ADR-002), the realistic estimate is 20-30 hours:

- ~80 output files per company instead of ~7
- 8 LLM prompts instead of 4 (ADR-004)
- A schema-validation layer for both `paperclip/v1` and `agentcompanies/v1`
- A use-case-pattern library (`solo_dev_shop.py`, `content_operations.py`, etc.)
- Test surface area scaled accordingly

A 20-30h v0.1 done as one block has two problems:

1. **Slow feedback.** No working artifact until ~hour 15+. If the prompt-and-template loop has a fundamental issue (e.g., the chosen Pydantic model shape doesn't render cleanly through Jinja, or the few-shot prompt design doesn't produce useful content), it's discovered late.
2. **Phase-discipline risk.** When a phase drags on, the temptation to pull v0.2 features forward grows. The original skeleton named "phase discipline" as the project's main risk control.

A two-sub-phase split is a known fix for both: ship a thin end-to-end slice first, then scale to full breadth on the second pass.

## Decision

v0.1 splits into two named sub-phases. Both must complete before v0.2 begins. Each has its own exit criteria.

### v0.1a — Single-agent slice (8-12 hours)

The smallest possible end-to-end flow that proves the architecture works.

**Inputs:** Full `input-template.md` filled in (operator can leave optional sections sparse).

**Outputs:** A bundle directory containing:

- `.paperclip.yaml` (1 agent in agents map, 0 projects)
- `COMPANY.md` (full content: Identity, We are, We are not, Constraints, Goals, North star)
- `README.md` (auto-generated, 1-agent mermaid)
- `LICENSE.txt`
- `agents/<slug>/AGENTS.md` + `SOUL.md` + `HEARTBEAT.md` + `TOOLS.md`
- `skills/<slug>/SKILL.md` (1 skill, the agent's primary)

**Built:**

- All Pydantic models (input, company, agent, skill, output)
- 5 prompts: `identity_generator`, `org_planner` (capped at 1 agent), `agents_generator`, `soul_generator`, `skill_generator`
- 5 Jinja templates for the templated files
- `bundle.py` orchestrator with a `--single-agent` CLI flag that bypasses operations/projects/tasks
- Validators for `paperclip/v1` and `agentcompanies/v1`
- Tests at the unit + smoke-integration level

**Exit criteria:**

1. The operator fills the input template, runs `blueprints generate --input ... --output ... --single-agent`, gets a bundle in 1-3 minutes.
2. `diff -r` against a reference company shows structurally identical scaffolding (same files, same frontmatter shape, same section headings).
3. The bundle imports into Paperclip without schema errors, even with only 1 agent.

### v0.1b — Full multi-agent bundle (12-18 hours)

Scales the v0.1a foundation to full company-config breadth.

**Inputs:** Same template.

**Outputs:** Full ~80-file bundle (everything in v0.1a plus OPERATIONS.md, PROJECT-INVENTORY.md, projects/, tasks/, additional skills, multi-agent org).

**Built (in addition to v0.1a):**

- 3 additional prompts: `operations_generator`, `project_generator`, `task_generator`
- 3 additional Pydantic models: `project.py`, `task.py`, `operations.py`
- 4 additional templates
- Use-case pattern library: `solo_dev_shop.py`, `content_operations.py`, `product_sprint.py`, `oss_maintenance.py`, `newsletter.py`, `niche_site.py`, `custom.py`
- `bundle.py` orchestrator updated for `asyncio.gather` parallelism across per-agent and per-leaf prompts
- Cost-tracking logger
- Cross-agent handoff-graph validator (warns on mismatches between agent A's `hands_to` and agent B's `receives_from`)
- Tests at the orchestration + full-integration level

**Exit criteria:**

1. The operator fills the input template, runs `blueprints generate --input ... --output ...`, gets a full bundle in 5-10 minutes.
2. `diff -r` against a reference company is structurally identical.
3. The bundle imports into Paperclip; all agents/projects/tasks load without schema errors.
4. The operator reads the bundle and concludes: "this is a useful starting point. I could deploy this manually within an evening."
5. The operator actually does that deploy (manual import + manual Hermes wiring) for one real test case and verifies the company runs.

## Rationale

Three benefits beyond the obvious "smaller chunks ship faster":

1. **The hardest design decisions live in v0.1a.** Pydantic model shape, prompt-to-template handoff, Jinja partial structure, schema validators. v0.1a forces these to be settled before they have to support multi-agent complexity. By the time v0.1b starts, the foundation is decided.

2. **v0.1a's output is independently useful.** A single-agent slice (e.g., a solo CEO with a research skill) is sometimes all an operator wants — a lightweight "company" for a personal project that doesn't justify a 14-agent org. If v0.1b stalls for any reason, v0.1a still delivers value.

3. **The split is observable in CLI surface.** The `--single-agent` flag stays in the CLI permanently. It becomes a useful debugging tool (fast iteration on COMPANY.md content without paying for full-bundle generation) and a useful production tool (when single-agent is all you need).

## Consequences

**Positive:**

- Feedback after ~10 hours instead of ~25
- Reduced phase-discipline risk — v0.1a's narrow scope is hard to creep
- v0.1a's tests and validators carry over directly to v0.1b
- `--single-agent` is a permanent feature, not just a phase artifact

**Negative:**

- One more CLI flag to document and maintain
- A few v0.1a design decisions may need revisiting in v0.1b once multi-agent surfaces (e.g., the `tools` field shape may need richer schema for multi-agent companies). Acceptable — refactoring is cheap relative to the cost of building blind.

**Risks accepted:**

- v0.1a's output without OPERATIONS.md is less useful than the full bundle. Some operators will start with v0.1a and want OPERATIONS.md immediately. Mitigation: v0.1a's exit criteria note that operators waiting for OPERATIONS.md should wait for v0.1b rather than treating v0.1a as "the product."
- The split may feel like over-engineering for a side project. We accept the cost in favor of the feedback-velocity benefit.

## Alternatives considered

1. **No split — ship v0.1 as one block.** Rejected for the reasons above.
2. **Three sub-phases (v0.1a single agent, v0.1b multi-agent without ops, v0.1c with ops).** Rejected — the marginal value of separating ops/projects/tasks from multi-agent is low; they tend to land together in practice.
3. **Ship v0.1a as the only v0.1, defer multi-agent to v0.2.** Rejected — multi-agent is the main value proposition of the tool; deferring it makes v0.1 not worth doing.
