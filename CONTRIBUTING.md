# Contributing to paperclip-blueprints

Thanks for your interest in contributing. This is a CLI tool that turns a
structured Markdown brief into a deployable Paperclip company bundle. It's a
small project with a focused scope — please read the project README and ADRs
(`docs/adr/`) for the project's design decisions before proposing larger changes.

## Development environment

Prerequisites:

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- An Anthropic API key with access to Claude Opus 4.8 and Claude Sonnet 4.6
  (only needed to run live generation or the integration tests — the unit
  suite mocks all API calls)

Set up:

```bash
git clone https://github.com/Grolea-HQ/paperclip-blueprints.git
cd paperclip-blueprints

# Create the virtual environment and install dependencies (including dev tools)
uv sync

# Provide your API key via a .env file (never commit this)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

The key is read from the `ANTHROPIC_API_KEY` environment variable only. The
tool never reads credentials from files passed on the command line, and `.env`
is gitignored — keep it that way.

See `SETUP.md` for the full installation guide.

## Running tests

```bash
uv run pytest
```

The default suite runs entirely against mocked Anthropic responses, so it needs
no API key and makes no network calls. Integration tests that make real API
calls are gated behind a flag and cost money to run:

```bash
uv run pytest --integration
```

Only run the integration suite when you have a funded API key and a specific
reason to exercise the live path.

## Linting and type checking

All of these must pass before a change is considered done:

```bash
uv run ruff check src tests     # lint
uv run ruff format src tests    # format (run this, not just check)
uv run pyright src tests        # type check
```

`ruff format` is a required gate, not just `ruff check` — run both. Type hints
are expected on all public functions, and pyright should be clean.

## Pull requests

- **Target `main`.** Branch from `main`, open your PR against `main`.
- **Include tests for new behavior.** Bug fixes should include a regression
  test that fails before the fix and passes after; new features need tests that
  exercise the new path. Tests mirror the source layout
  (`src/paperclip_blueprints/cli.py` → `tests/test_cli.py`).
- **Pass all gates.** `ruff check`, `ruff format`, `pyright`, and `pytest` must
  all be green. CI runs the same checks.
- **One logical change per PR.** Keep PRs reviewable; split unrelated changes.
- **Document structural decisions.** If your change makes an architectural
  decision (new module, dependency, format change), add an Architecture
  Decision Record under `docs/adr/` using `docs/adr/000-template.md`. Adding a
  dependency to `pyproject.toml` requires an ADR.

## Working conventions

### A brief-schema change carries its template update

Any change that adds, removes or alters a field in `CompanyBrief` MUST update
`examples/input-template.md` in the same change — a brief field an operator
cannot discover does not exist.

If a change touches `src/paperclip_blueprints/models/input.py`, it must also
touch `examples/input-template.md`.

### State what is true, not how we got it wrong

Committed artifacts — ADRs, specs, contracts — record the current fact. An
amendment names what is struck, what is true instead, and where the design now
lives.

Reasoning earns its place only when it changes what a future reader does.
Commentary on why a mistake was tempting, or how it felt to find, does not:
these files are read by people and sessions with no memory of the conversation
that produced them.

## Filing bugs and feature requests

Issues are tracked in [GitHub Issues](https://github.com/Grolea-HQ/paperclip-blueprints/issues).

- **Bugs** — open an issue describing what you did, what you expected, and what
  actually happened. Include the command you ran, the relevant output, and your
  Python and tool versions. If a generated bundle fails Paperclip import, include
  the validator output `generate` printed (and, if generation was rejected, the
  contents of the `<output>-failed/` directory it wrote).
- **Feature requests** — open an issue describing the use case and why the
  current behavior is insufficient. Because the project is deliberately scoped
  to Paperclip configuration generation, proposals that broaden scope are likely
  out of bounds. Out of scope: features documented as future phases,
  runtime-specific tooling, things that should live in Paperclip core. But the
  conversation is welcome.

New issues start with a `needs-triage` label; a maintainer will evaluate and
re-label.

## A note on prompt changes

The hardest and most consequential part of this project is the LLM prompts in
`src/paperclip_blueprints/prompts/`. They are versioned in git and treated as
source code.

If your change modifies a prompt, **include a sample bundle output (or the
relevant excerpt) demonstrating the change's effect** in the PR. A prompt diff
alone doesn't show whether the output got better — reviewers need to see the
before/after of what the model actually produces. A short before/after excerpt
of the affected file (e.g. the `Goals` section of a `COMPANY.md`, or an
`AGENTS.md` decision-rights block) is enough; you don't need to attach a full
~80-file bundle.

Watch especially for the "recycled-shape" failure mode: if outputs start looking
like a generic template with names swapped, the prompt is over-fitting and the
change needs rework.

## Code of conduct

Be respectful and constructive. This is a personal project released in good
faith; assume good intent and keep discussion focused on the work.
