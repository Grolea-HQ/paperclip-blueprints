# Paperclip Blueprints

[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built for Paperclip](https://img.shields.io/badge/built%20for-Paperclip-7b3fe4)](https://github.com/paperclipai/paperclip)

A CLI tool that takes a structured Markdown brief and generates a complete, deployable **Paperclip company bundle** — a directory of ~80 files conforming to the `paperclip/v1` and `agentcompanies/v1` schemas, ready to import into a Paperclip instance.

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

Later phases automate the actual deployment: creating the Paperclip company via API (v0.2), provisioning Hermes on a target VPS (v0.3).

## Why this exists

Setting up a Paperclip + Hermes company manually involves:

- Writing strong identity content (Identity, We are, We are not, Constraints) — hard, requires synthesis. The tool does this from a brief.
- Designing the org chart with reasonable span-of-control and clear escalation paths — easy to get wrong. The tool applies canonical use-case patterns (solo dev shop, content ops, etc.) or freeform plans.
- Configuring the Paperclip side correctly (10 documented integration gaps that break things) — v0.2 automates this.
- Configuring the Hermes side correctly (6 more gaps) — v0.3 automates this.
- Wiring them together (more gaps, mostly undocumented) — v0.3 automates this.

The first parts benefit from frontier-model synthesis. The latter parts are mechanical but easy to get wrong. The tool handles both.

## Status

**v0.1 complete.** v0.1a (single-agent slice) and v0.1b (full multi-agent bundle) are built and verified — generated bundles import successfully into a real Paperclip instance. Deployment automation (v0.2 Paperclip API, v0.3 Hermes-on-VPS) is planned but not yet built.

## Quickstart

```bash
# Clone and install
git clone https://github.com/Grolea-HQ/paperclip-blueprints.git
cd paperclip-blueprints
uv sync

# Provide your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Set up your input brief
cp examples/input-template.md my-company-brief.md
# Edit my-company-brief.md to describe identity, north star, goals, constraints

# Generate the bundle
uv run blueprints generate --input my-company-brief.md --output my-company/

# Inspect the bundle
ls my-company/
cat my-company/COMPANY.md

# Import into Paperclip via the UI's import flow (v0.2 will automate the deploy)
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- Anthropic API key (`ANTHROPIC_API_KEY` env var)
- A Paperclip instance (for v0.2+ deployment)
- A target VPS with SSH access (for v0.3 full deployment)

## Tech stack

- Python 3.11+, Typer (CLI), Pydantic v2 (validation), Jinja2 (templating), ruamel.yaml (YAML round-trips)
- Anthropic SDK (LLM access — Claude Opus 4.7 and Sonnet 4.6)

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
- **Default to native, not Docker.** Native Hermes deployment skips 5 container-specific gaps. Docker is an opt-in v0.3 mode.
- **Phase discipline is the project's main risk control.** Don't pull v0.2/v0.3 work into v0.1 scope.

## License

MIT. See LICENSE.

## Acknowledgments

- [Paperclip](https://paperclip.community) — autonomous company management platform
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — the agent runtime

Encodes patterns from real Paperclip + Hermes deployment experience.
