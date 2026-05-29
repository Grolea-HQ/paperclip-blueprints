# ADR-004 — Prompt Architecture

**Status:** Accepted
**Date:** Pre-v0.1, during the rework
**Relates to:** ADR-002 (output bundle format), ADR-003 (input template format), ADR-005 (phase split)

---

## Context

The original project skeleton specified 4 prompts: `spec_generator`, `org_planner`, `soul_generator`, `agents_generator`, plus a `deployment_planner`. With the corrected output bundle format (ADR-002), the work splits differently:

- Some output files are pure templates (no LLM call): HEARTBEAT.md, README.md, `.paperclip.yaml`, LICENSE.txt, parts of TOOLS.md
- Some output files are short, schema-heavy LLM-generated content (PROJECT.md, TASK.md)
- Some output files are long, persona-heavy LLM-generated content (SOUL.md, COMPANY.md, AGENTS.md, OPERATIONS.md)
- The per-skill SKILL.md files are a new content type the original prompts didn't cover

We need a prompt architecture that:

1. Matches the right model tier (Opus vs Sonnet) to each content type
2. Parallelizes safely (per-agent and per-leaf prompts are independent once the org plan is fixed)
3. Enforces structural rules at the right layer (some via prompt instructions, some via post-generation validators)
4. Keeps prompt files versioned in git as `.md` files (per the original tech stack ADR)

## Decision

Eight prompts, organized in a directed graph:

```
                  ┌──────────────────┐
input CompanyBrief│identity_generator│ → CompanyDefinition (COMPANY.md content)
                  └──────────────────┘                 │
                          │                             │
                          ▼                             │
                  ┌──────────────────┐                  │
                  │ org_planner      │ → List[Stub]     │
                  └──────────────────┘                  │
                          │                             │
              ┌───────────┼────────────┬──────────┬─────┴────────┐
              ▼           ▼            ▼          ▼              ▼
     ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
     │agents_gen  │ │soul_gen  │ │skill_gen │ │proj_gen│ │task_gen  │
     │(per agent) │ │(per agnt)│ │(per skl) │ │(per pj)│ │(per task)│
     └────────────┘ └──────────┘ └──────────┘ └────────┘ └──────────┘
              │           │            │          │              │
              └───────────┴────────────┴──────────┴──────────────┘
                                       │
                                       ▼
                              ┌──────────────────────┐
                              │ operations_generator │ → OperationsDefinition
                              └──────────────────────┘    (echoes constraints
                                                           from CompanyDefinition)
```

### Prompt-by-prompt details

| Prompt | Model | Input | Output | Parallelism |
|---|---|---|---|---|
| `identity_generator` | Opus + extended thinking | `CompanyBrief` | `CompanyDefinition` (Identity, We are, We are not, Constraints, Goals, North star) | Single call |
| `org_planner` | Sonnet | `CompanyBrief` + `CompanyDefinition` + use-case pattern (if any) | `List[AgentStub]` with slug, name, title, reports_to, skills[] | Single call |
| `agents_generator` | Sonnet | One `AgentStub` + `CompanyDefinition` + governance-spectrum position | One full `AgentDefinition` (mandate, triggers, handoffs, deliverables, decision rights, escalation) | One call per agent, parallel |
| `soul_generator` | Opus | One `AgentStub` + `CompanyDefinition` | One `AgentSoul` (7-section persona) | One call per agent, parallel |
| `skill_generator` | Sonnet | One skill slug + context from agents that use it | One `SkillDefinition` (when to load, inputs, procedure, outputs, anti-patterns, references) | One call per skill, parallel |
| `project_generator` | Sonnet | One project context + `CompanyDefinition` | One `ProjectDefinition` (description, success_condition) | One call per project, parallel |
| `task_generator` | Sonnet | One task context + parent project + assignee | One `TaskDefinition` (objective, completion_criteria) | One call per task, parallel |
| `operations_generator` | Opus | `CompanyDefinition` + agent list + project list | `OperationsDefinition` (phase model, idle-state, approval rules, anti-drift checks echoing constraints, routine slots) | Single call, runs last |

### Pure templates (no LLM call)

These output files are rendered from Pydantic models by Jinja2 with no Anthropic call:

- `HEARTBEAT.md` — identical stub content per agent, with only the agent's title substituted
- `TOOLS.md` — Paperclip API block + file system block + conventions block; the role-specific tools paragraph comes from the agent's `tools` field (which `agents_generator` produces a short string for)
- `README.md` — auto-generated from the agent list and project list; mermaid org chart from `reports_to` graph
- `.paperclip.yaml` — schema/sidebar/agents-map/projects-map from the agent and project lists
- `PROJECT-INVENTORY.md` — seeded from the generated projects/tasks; "completed" and "in-flight" tables start empty
- `LICENSE.txt` — copied from a template, operator-configurable

### Model-tier rationale

- **Opus for identity/persona content** (`identity_generator`, `soul_generator`, `operations_generator`): these prompts require synthesis quality. The COMPANY.md and SOUL.md content is what agents read on every wakeup; quality matters more than cost.
- **Sonnet for structural/handoff content** (`org_planner`, `agents_generator`, `project_generator`, `task_generator`, `skill_generator`): these are more constrained — slugs, role definitions, success criteria. Sonnet is sufficient at substantially lower cost.

The CLI `--model` flag overrides defaults per run, useful for iteration.

### Parallelism

For a typical 14-agent company:

- 2 sequential calls (identity, org_planner) → ~1 minute
- 14 + 14 + ~10 + ~3 + ~6 parallel calls = ~47 calls fanning out — gated by Anthropic's rate limits but typically ~2 minutes wall-clock if rate limits allow
- 1 sequential call (operations_generator) → ~30 seconds
- Total wall-clock: 3-5 minutes for a full bundle

Without parallelism, this would be ~25 minutes serially. Parallelism is worth the orchestration complexity.

## Consequences

**Positive:**

- Each prompt has a narrow, testable scope. Easier to iterate on prompt quality.
- Mixed model tiers reduce cost without sacrificing quality where it matters.
- Parallelism makes the generation feel snappy (3-5 minutes vs 25 minutes).
- Prompt files versioned in git → prompt eval diffs are clean.

**Negative:**

- More prompts to maintain. Each one needs example fixtures, mocked-API tests, and integration-test coverage.
- Orchestration code in `bundle.py` is non-trivial — need to handle partial failures (e.g., 13 of 14 agent-prompt calls succeed; what's the right behavior?). Decision: any failure aborts the run; the operator re-runs. Idempotency is a v0.2 concern.
- Per-prompt cost tracking is more complex than a single-prompt design. Acceptable; the cost telemetry helps the operator decide when to switch model tiers.

**Risks accepted:**

- A 14-agent company makes 47 parallel API calls. If Anthropic's rate limits tighten, this needs to be re-paced. Mitigation: configurable concurrency cap (default 10), retry-with-backoff on 429s.
- Cross-agent consistency (e.g., does the CEO's "hands_to" list match the CTO's "receives_from" list?) is not automatically enforced because each agent is generated in isolation. Mitigation: post-generation validator that cross-checks the handoff graph and warns on mismatches. The operator can re-run or accept warnings.

## Alternatives considered

1. **Single mega-prompt that produces the whole bundle.** Rejected — context window limits, no parallelism, no model-tier mixing, no narrow testability.
2. **4 prompts as in the original skeleton.** Rejected — doesn't cover the new content types (SKILL.md, PROJECT.md, TASK.md, OPERATIONS.md) or the COMPANY.md-specific identity content.
3. **Use a framework like LangChain or DSPy for orchestration.** Rejected — direct Anthropic SDK + asyncio is sufficient, doesn't lock us into a framework's update cycle, and matches the "no abstraction layer" principle in the tech stack ADR.
4. **Generate skills first, then use the skill list as context for agents.** Considered. Rejected because skills are typically named in the org_planner's output (e.g., "newsletter-voice-capture is owned by Managing Editor"). The dependency goes org_planner → skill_generator and agents_generator in parallel, not the reverse.
