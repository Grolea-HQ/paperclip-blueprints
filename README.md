# Paperclip Blueprints

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

**Pre-v0.1.** Project skeleton and planning documents exist. Implementation hasn't started.

See `MASTER_PROMPTS.md` for the three-phase build plan. v0.1 is split into v0.1a (single-agent slice, 8-12h) and v0.1b (full multi-agent bundle, 12-18h).

## Quickstart (when v0.1 ships)

```bash
# Install
uv tool install paperclip-blueprints

# Set up your input brief
cp examples/input-template.md my-company-brief.md
# Edit my-company-brief.md to describe identity, north star, goals, constraints

# Generate the bundle
blueprints generate --input my-company-brief.md --output my-company/

# Inspect the bundle
ls my-company/
cat my-company/COMPANY.md

# Import into Paperclip via the UI's import flow, or wait for v0.2 to automate the deploy
```

Until v0.1 ships, this section is aspirational. See `MASTER_PROMPTS.md` for current phase status.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- Anthropic API key (`ANTHROPIC_API_KEY` env var)
- A Paperclip instance (for v0.2+ deployment)
- A target VPS with SSH access (for v0.3 full deployment)

## Tech stack

- Python 3.11+, Typer (CLI), Pydantic v2 (validation), Jinja2 (templating), ruamel.yaml (YAML round-trips)
- Anthropic SDK (LLM access — Claude Opus 4.7 and Sonnet 4.6)
- [spec-kit](https://github.com/github/spec-kit) for development workflow
- [mattpocock/skills](https://github.com/mattpocock/skills) for engineering practices

## Project layout

```
CLAUDE.md                    # Claude Code's operating context for this codebase
MASTER_PROMPTS.md            # Three-phase build plan (v0.1a, v0.1b, v0.2, v0.3)
SETUP.md                     # Installation + daily usage
examples/
├── input-template.md        # Canonical input format (mirrors COMPANY.md structure)
├── reference-companies/     # newsletter-press, niche-site-empire — structural references
└── generated-companies/     # Blueprints outputs (gitignored except sanitized examples)
docs/
├── deployment-gaps.md       # ~22 Paperclip+Hermes integration gaps + best-practice patterns
└── adr/                     # Architecture Decision Records
src/paperclip_blueprints/            # Built during v0.1
├── models/                  # Pydantic schemas
├── prompts/                 # System prompts as .md files
├── generators/              # Anthropic API callers
├── templates/               # Jinja2 templates for pure-template files
├── renderers/               # Pydantic → Markdown rendering
├── patterns/                # Canonical use-case patterns (solo-dev-shop, content-ops, etc.)
├── validators/              # Schema validation for paperclip/v1 and agentcompanies/v1
└── deployers/               # v0.2+ Paperclip API integration
```

## Philosophy

- **Output bundle matches Paperclip's import format precisely.** The two reference companies in `examples/reference-companies/` are the canonical "what good looks like" for structure. Prompts produce original content; templates ensure structural fidelity.
- **Goal-as-outcome rule.** Goals in the input are persistent outcomes, not one-off tasks. The blueprints validates this at input time.
- **Default to native, not Docker.** Native Hermes deployment skips 5 container-specific gaps. Docker is an opt-in v0.3 mode.
- **Spec-Driven Development.** Use [spec-kit](https://github.com/github/spec-kit) commands for feature work.
- **Disciplined micro-practices.** Use selected [mattpocock/skills](https://github.com/mattpocock/skills) for execution discipline.
- **Phase discipline is the project's main risk control.** Don't pull v0.2/v0.3 work into v0.1 scope.

See `CLAUDE.md` for the full operating brief.

## License

Not yet decided. Personal-tool phase. MIT is the likely choice if/when it goes open-source.

## Acknowledgments

- [Paperclip](https://paperclip.community) — autonomous company management platform
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — the agent runtime
- [github/spec-kit](https://github.com/github/spec-kit) — Spec-Driven Development toolkit
- [mattpocock/skills](https://github.com/mattpocock/skills) — engineering practice skills

Built by an operator running a production Paperclip + Hermes company elsewhere, encoding lessons learned from real deployment experience.
