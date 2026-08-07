# Paperclip Blueprints

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built for Paperclip](https://img.shields.io/badge/built%20for-Paperclip-7b3fe4)](https://github.com/paperclipai/paperclip)

A CLI tool that takes a structured Markdown brief and generates a complete, deployable **Paperclip company bundle** — a directory of files conforming to the `paperclip/v1` and `agentcompanies/v1` schemas, ready to import into a Paperclip instance.

> 📖 **Walkthrough:** [How to use Paperclip Blueprints](https://www.grolea.com/insights/how-to-use-paperclip-blueprints) — a step-by-step guide to writing a brief and generating your first bundle.

## What this does

Give the tool a brief describing a company's identity, north star, goals, and constraints. It produces a directory tree matching Paperclip's import format:

- `.paperclip.yaml` (runtime config: sidebar, per-agent adapter/model/budget, per-agent run-policy caps, the board-approval company setting, and routines for scheduled work)
- `COMPANY.md` (Identity, We are, We are not, Constraints, Goals, North star)
- `README.md` (auto-generated overview with mermaid org chart)
- `OPERATIONS.md` (operator-facing operating manual — phase model, idle-state protocol, approval rules, anti-drift; **human docs**, not read by agents)
- `PROJECT-INVENTORY.md` (starter projects, in-flight + completed tables)
- `agents/<slug>/` per agent: `AGENTS.md`, `SOUL.md`, `HEARTBEAT.md`, `TOOLS.md`
- `projects/<slug>/PROJECT.md` per starter project
- `tasks/<slug>/TASK.md` per starter task (a scheduled task is flagged `recurring` and gets a matching routine)
- `skills/<slug>/SKILL.md` per shared skill
- `LICENSE.txt`

The result is a Paperclip-importable bundle ready to use.

**How governance reaches agents (ADR-022).** A UI-imported company is database-backed — there is no company-root filesystem for agents to read. So the constitution and rules each agent enforces are folded into its `AGENTS.md` (the carrier the import surfaces to the agent), the board-approval gate ships as a `.paperclip.yaml` company setting, and schedule-driven work becomes routines. `OPERATIONS.md` stays as the operator's readable operating manual, not an agent-facing file.

**Per-agent run-policy caps (ADR-034).** Each agent gets a turn cap and concurrent-run limit derived from its role. Section 12 of the brief overrides them per agent — including turning a heartbeat off so an agent runs only on demand. Leave the section blank to keep the defaults.

**Routine scheduling (ADR-036).** The brief states cadence, not clock time, so each routine's time of day is derived deterministically from its task slug — the same brief always produces the same schedule. Routines that still land on the same trigger, and consumers scheduled at or before the producer they name, are reported as warnings for you to judge; neither blocks generation.

**Routine timezone (ADR-038).** Section 9 of the brief takes an optional IANA timezone (e.g. `Europe/Helsinki`); every routine is scheduled in it. Leave it blank for UTC. Because routine times are spread across the working day, binding your zone is what makes that window your hours rather than UTC's. A zone name the database does not recognise stops the run before any generation happens, so a typo costs nothing.

## Operating canon (section 11)

Section 11 of the brief is for the rules your agents should actually follow — procedures, rubrics, thresholds, domain decision rules. It is the one input with no other carrier, so it is threaded **whole and unmodified** into every generator that writes procedure (skills, agent mandates, tasks, projects), with an instruction to **encode it into procedure rather than summarise it** (ADR-037).

Because it is encoded rather than paraphrased, an offhand aside written there comes back as procedure too. Write it as canon or leave it out.

After the bundle is rendered, each canon item is checked for reach and the run prints one line per item that fell short:

| Verdict | Meaning |
|---|---|
| carried | the item appears in two or more generated files — no output |
| thin | it appears in exactly one file, which is named so you can judge it |
| missing | it appears in no generated file at all |
| coverage unknown | the item is named by a sentence rather than a phrase, so it cannot be searched for |

These are **advisory** — they never block generation, and they report *reach*, never quality. Whether a rubric landed as usable procedure is a judgement only you can make by reading the bundle.

The check finds canon items by their markdown marking, so how you mark section 11 determines what can be verified. `examples/input-template.md` documents the convention.

## Why this exists

Setting up a Paperclip company manually involves:

- Writing strong identity content (Identity, We are, We are not, Constraints) — hard, requires synthesis. The tool does this from a brief.
- Designing the org chart with reasonable span-of-control and clear escalation paths — easy to get wrong. The tool applies canonical use-case patterns (solo dev shop, content ops, etc.) or freeform plans.

The tool handles the synthesis from a brief and produces a deployable bundle that imports directly into Paperclip.

## Status

**v0.1 complete.** Generated bundles import successfully into a real Paperclip instance. The tool is in production use.

## Cost

Generating a bundle costs roughly **$1–3 in Anthropic API credits**, depending on company complexity (an 11-agent bundle runs about $1.50 at current pricing). Generation typically takes **3–8 minutes**, again depending on complexity — a research-digest bundle runs about 5 minutes. The tool prints a cost summary after each run. Note this uses Anthropic API credits, not a Claude subscription.

## Quickstart

```bash
# Clone and install
git clone https://github.com/Grolea-HQ/paperclip-blueprints.git
cd paperclip-blueprints
uv sync

# Provide your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Set up your input brief
cp examples/input-template.md examples/my-company-brief.md
# Edit examples/my-company-brief.md to describe identity, north star, goals, constraints (see examples/example-brief-*.md for references)

# Generate the bundle (takes 3-8 minutes, costs ~$1-3 in API credits)
uv run blueprints generate --input examples/my-company-brief.md --output examples/generated-companies/my-company/

# Inspect the bundle
ls examples/generated-companies/my-company/
cat examples/generated-companies/my-company/COMPANY.md

# Re-check the bundle's operating-canon coverage at any time (no API key, no generation)
uv run blueprints check-canon --input examples/my-company-brief.md --bundle examples/generated-companies/my-company/

# Import into Paperclip via the UI's import flow
```

> **Re-importing?** Import into a **fresh** target — e.g. `companies.sh add --target new
> --include company,agents,projects,tasks,skills`. Importing over an existing company
> uses Paperclip's default collision strategy, which silently duplicates entities
> (`-2`-suffixed agents/projects). On the generation side, `blueprints generate`
> refuses a non-empty `--output` directory unless you pass `--force` (which cleanly
> replaces it — it never merges two generations).

## Examples

The `examples/` directory contains:

- `input-template.md` — the blank brief template. Start here and fill in your company's details.
- `example-brief-research-digest.md` — a worked example for a research newsletter company.
- `example-brief-indie-game-studio.md` — a worked example for an indie game studio.

Both worked examples show the level of detail that produces coherent bundles. Use them as references when writing your own brief.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- Anthropic API key (`ANTHROPIC_API_KEY` env var)
- A Paperclip instance to import the generated bundle into

## Tech stack

- Python 3.11+, Typer (CLI), Pydantic v2 (validation), Jinja2 (templating), ruamel.yaml (YAML round-trips)
- Anthropic SDK (LLM access — Claude Opus 4.8 and Sonnet 4.6)

## Project layout

```
README.md                    # This file
SETUP.md                     # Installation + daily usage
CONTRIBUTING.md              # How to contribute
CONTEXT.md                   # Domain glossary + conventions
LICENSE                      # MIT
examples/
├── input-template.md        # Canonical input format (mirrors COMPANY.md structure)
└── generated-companies/     # Blueprints outputs (gitignored except sanitized examples)
docs/
└── adr/                     # Architecture Decision Records
src/paperclip_blueprints/
├── models/                  # Pydantic schemas
├── prompts/                 # System prompts as .md files
├── generators/              # Anthropic API callers
├── templates/               # Jinja2 templates for pure-template files
├── renderers/               # Pydantic → Markdown rendering
├── patterns/                # Canonical use-case patterns (solo-dev-shop, content-ops, etc.)
└── validators/              # Schema validation for paperclip/v1 and agentcompanies/v1
tests/                       # pytest suite
```

## Philosophy

- **Output bundle matches Paperclip's import format precisely.** Structural fidelity is enforced by validators on every generation.
- **Goal-as-outcome rule.** Goals in the input are persistent outcomes, not one-off tasks. The blueprints validates this at input time.
- **Patterns come from Paperclip's community guides.** Identity structure, "we are" / "we are not" framing, span-of-control discipline. The tool's value is automating their application, not inventing the patterns.

## License

MIT. See LICENSE.

## Acknowledgments

- [Paperclip](https://paperclip.ing) — autonomous company management platform

Built by [Grolea Oy](https://grolea.com). Encodes patterns from Paperclip's community guides, refined through real deployment experience.
