# ADR-001: Tech stack choices for paperclip-blueprints

## Status

Accepted

## Date

2026-05-22

## Context

The Paperclip Blueprints is a CLI tool that generates Paperclip + Hermes Agent company configurations using LLM-powered synthesis. It needs:

- A language and runtime
- A package manager
- A CLI framework
- LLM API access
- Templating for output files
- Data validation
- Testing infrastructure
- Type checking
- Linting and formatting

These choices set the foundation for all subsequent development. Documenting them up front prevents bikeshedding later and gives Claude Code clear direction.

## Decision

**Language and runtime: Python 3.11+**
- Matches spec-kit's prerequisites
- Matches the Hermes Agent ecosystem (the tool's output target)
- Mature ecosystem for the tooling we need
- The operator has Python experience

**Package manager: uv**
- Faster than pip/pip-tools/poetry
- spec-kit's documented prerequisite
- Lockfile handling is clean
- Single tool for venv + dependency management

**CLI framework: Typer**
- Type hints drive the CLI definition (less boilerplate than Click)
- Built on Click, so Click's extension ecosystem is available
- Rich integration for output formatting
- Modern, well-maintained

**LLM access: Anthropic SDK direct**
- The operator has direct Anthropic access (Max 5 plan)
- No need for an abstraction layer (LangChain, LlamaIndex) — adds complexity without value at this scope
- Direct SDK lets us use extended thinking, streaming, and other Anthropic-specific features
- One model provider keeps the project simple

**Templating: Jinja2**
- Industry standard
- Preserves structure of output files
- Well-documented
- Familiar to most Python developers

**Data validation: Pydantic v2**
- Catches malformed input before it reaches the LLM (saves API cost on bad inputs)
- Type hints integrate with Typer naturally
- v2 is significantly faster than v1
- Excellent error messages for end users

**YAML handling: ruamel.yaml**
- Preserves comments in YAML files (PyYAML loses them)
- Preserves ordering and formatting
- Critical for generated `routines.yml` files that operators may want to read and edit

**Testing: pytest**
- Standard
- Integrates with mattpocock/tdd skill
- Rich plugin ecosystem (pytest-mock, pytest-cov, etc.)

**Linting and formatting: ruff**
- Single tool replaces black + flake8 + isort + others
- Extremely fast
- Active development
- One config file (`pyproject.toml`)

**Type checking: pyright**
- Faster than mypy
- Better IDE integration (Pylance uses pyright)
- More accurate for modern Python (Literal types, TypedDict, etc.)
- The choice is close to a coin-flip with mypy; pyright wins on speed

## Consequences

### Positive consequences
- Modern, well-maintained tooling throughout
- Tight integration between layers (Typer + Pydantic types align naturally)
- Fast dev loop (uv is fast, ruff is fast, pyright is fast)
- Choices align with spec-kit's tooling (Python, uv)
- Single LLM provider keeps logic simple

### Negative consequences
- Locked into Anthropic for now. If we want to support OpenAI or others later, we'll need to add an abstraction layer or rewrite call sites
- Pydantic v2 has different APIs from v1; some Stack Overflow answers will be wrong
- ruamel.yaml has more API surface than PyYAML; takes longer to learn

### Neutral consequences
- The operator has familiarity with this stack already (no significant learning curve)
- These choices are common enough that Claude Code has good training data on them

## Alternatives considered

- **Node.js / TypeScript:** Could work, but spec-kit is Python-first and the Hermes ecosystem is Python. Switching languages would create friction at integration points.
- **Click instead of Typer:** Mature and widely used, but more boilerplate. Typer is strictly better for new projects.
- **LangChain or similar LLM framework:** Adds abstraction complexity without value at this project's scope. Direct Anthropic SDK is simpler and exposes more of Anthropic's capabilities.
- **mypy instead of pyright:** Fine alternative; rejected on speed grounds. If the operator strongly prefers mypy, switching is low-effort.
- **black + flake8 instead of ruff:** Rejected on speed and tool-count grounds. ruff is the modern consolidation.

## References

- [Typer documentation](https://typer.tiangolo.com/)
- [Pydantic v2 docs](https://docs.pydantic.dev/)
- [ruff documentation](https://docs.astral.sh/ruff/)
- [uv documentation](https://docs.astral.sh/uv/)
- [spec-kit prerequisites](https://github.com/github/spec-kit#-prerequisites)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
