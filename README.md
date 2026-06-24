# Paperclip Blueprints

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built for Paperclip](https://img.shields.io/badge/built%20for-Paperclip-7b3fe4)](https://github.com/paperclipai/paperclip)

A CLI tool that takes a structured Markdown brief and generates a complete, deployable **Paperclip company bundle** — a directory of files conforming to the `paperclip/v1` and `agentcompanies/v1` schemas, ready to import into a Paperclip instance.

> 📖 **Walkthrough:** [How to use Paperclip Blueprints](https://www.grolea.com/insights/how-to-use-paperclip-blueprints) — a step-by-step guide to writing a brief and generating your first bundle.

## What this does

Give the tool a brief describing a company's identity, north star, goals, and constraints. It produces a directory tree matching Paperclip's import format:

- `.paperclip.yaml` (runtime config: sidebar, agents map, projects map)
- `COMPANY.md` (Identity, We are, We are not, Constraints, Goals, North star)
- `README.md` (auto-generated overview with mermaid org chart)
- `OPERATIONS.md` (phase model, idle-state protocol, approval rules, anti-drift checks)
- `PROJECT-INVENTORY.md` (starter projects, in-flight + completed tables)
- `agents/<slug>/` per agent: `AGENTS.md`, `SOUL.md`, `HEARTBEAT.md`, `TOOLS.md`
- `projects/<slug>/PROJECT.md` per starter project
- `tasks/<slug>/TASK.md` per starter task
- `skills/<slug>/SKILL.md` per shared skill
- `LICENSE.txt`

The result is a Paperclip-importable bundle ready to use.

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
