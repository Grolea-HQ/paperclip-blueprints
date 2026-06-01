# SETUP.md — Installation and daily usage

This guide covers getting the paperclip-blueprints project running on a fresh machine and the daily workflow once it's set up.

---

## First-time installation

### Prerequisites

- Python 3.11 or newer (`python3 --version`)
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 20+ (for installing the mattpocock/skills via npx — only needed for development discipline, not for running the tool)
- An Anthropic API key with access to Claude Opus 4.7 and Sonnet 4.6
- (Optional, for v0.2+) Access to a running Paperclip instance with an admin token
- (Optional, for v0.3) An SSH-able target VPS

### Clone and bootstrap

```bash
git clone git@github.com:Grolea-HQ/paperclip-blueprints.git
cd paperclip-blueprints

# Set up Python environment
uv sync

# Set up spec-kit (Claude Code integration)
# IMPORTANT: install from git, not PyPI. The `specify-cli` name on PyPI is a
# different project and will fail when it tries to fetch template assets.
# The real spec-kit lives at github/spec-kit. Pin the version explicitly;
# check https://github.com/github/spec-kit/releases for the current tag.
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.8.11
specify init . --integration claude

# Install the mattpocock skills working set
# (See .claude/commands/start-session.md for the exact list)

# Configure your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Install pre-commit hooks
pre-commit install
```

### Verify the install

```bash
# Lint and type check pass
uv run ruff check src tests
uv run pyright src tests

# Smoke tests pass
uv run pytest tests/test_smoke.py
```

If any of those fail on a clean install, that's a setup bug — open an issue or check the troubleshooting section below.

---

## Daily workflow

### Generating a company bundle (when v0.1 is done)

```bash
# 1. Copy the input template
cp examples/input-template.md my-brief.md

# 2. Fill it in — see the template's inline guidance and the validation checklist
# Pay particular attention to:
# - North star must be a measurable persistent outcome, not a task
# - "We are not" needs at least 2 entries (anti-drift framing)
# - Constraints are non-negotiable rules, not soft preferences

# 3. Generate
blueprints generate --input my-brief.md --output examples/generated-companies/my-company/

# 4. Inspect the bundle
ls examples/generated-companies/my-company/
cat examples/generated-companies/my-company/COMPANY.md
cat examples/generated-companies/my-company/README.md   # Mermaid org chart inside

# 5. Compare structure to a canonical example
# (Reference companies are no longer bundled in this repo — see ADR-011.
#  Download one from https://paperclip.community/companies to diff against.)
diff -r ~/Downloads/newsletter-press/ \
        examples/generated-companies/my-company/ | head -50
```

For v0.1a single-agent runs, add `--single-agent`:

```bash
blueprints generate --input my-brief.md --output my-test/ --single-agent
```

### Validating an input without generating

```bash
blueprints validate --input my-brief.md
```

This runs the input through Pydantic schemas and the goal-as-outcome / span-of-control rules without making any Anthropic API calls. Use it for fast iteration on the brief.

### Previewing only COMPANY.md (fail-fast)

```bash
blueprints preview --input my-brief.md
```

Generates only the COMPANY.md content. ~30 seconds, one Opus call. Useful for iterating on identity content before paying for a full bundle generation.

### Deploying to Paperclip (when v0.2 is done)

```bash
blueprints deploy \
  --bundle examples/generated-companies/my-company/ \
  --paperclip-url http://100.127.11.16:3100 \
  --paperclip-token-env PAPERCLIP_ADMIN_TOKEN

# Then follow the generated post-deploy checklist
cat examples/generated-companies/my-company/post_deploy_checklist.md
```

### Full deployment to a VPS (when v0.3 is done)

```bash
blueprints launch \
  --input my-brief.md \
  --target ssh://operator@my-vps.example.com

# Or with Docker mode (not recommended; adds 5 container-specific gaps)
blueprints launch \
  --input my-brief.md \
  --target ssh://operator@my-vps.example.com \
  --mode docker
```

---

## Development workflow

This project uses spec-kit + mattpocock skills. See `.claude/commands/start-session.md` for the session protocol.

### Starting a new feature

```bash
# In Claude Code
/speckit.specify   # Define what the feature does
/speckit.plan      # Add technical implementation
/speckit.tasks     # Break into discrete units
/speckit.implement # Execute
```

### Before any architectural decision

```bash
# In Claude Code
/grill-with-docs   # Get questioned on the decision against domain docs
```

Then add an ADR in `docs/adr/`.

### During hard bugs

```bash
# In Claude Code
/diagnose          # Disciplined debugging loop
```

### End of session

```bash
# In Claude Code
/handoff           # If context might be lost before next session

# In terminal
uv run ruff check src tests
uv run ruff format src tests
uv run pyright src tests
uv run pytest
git status         # Operator decides what to commit
```

---

## Troubleshooting

### `uv sync` fails on first install

Verify Python 3.11+. uv resolves against the version in `pyproject.toml`; older Python versions will fail at resolve time.

### Anthropic API calls fail with 401

Check `ANTHROPIC_API_KEY` is set in `.env` and that the key has access to both `claude-opus-4-7` and `claude-sonnet-4-6` models. Most Anthropic keys do; if yours doesn't, check the Console.

### Generated bundle fails Paperclip import

Run schema validation in isolation:

```bash
blueprints validate-bundle --bundle examples/generated-companies/my-company/
```

This runs the same validators that should have run before the bundle was written. If it passes here but fails at Paperclip import, the import format may have changed — check the Paperclip docs and update `src/paperclip_blueprints/validators/`.

### Prompts produce output that looks like a reference company

If outputs are too similar to `newsletter-press` or `niche-site-empire` (the few-shot references in prompts), the prompt is over-fitting. Compare:

1. Are the few-shot blocks too long? Trim to the structural skeleton.
2. Are the prompts including verbatim multi-paragraph content from the references? Replace with paraphrased / structural-only examples.
3. Is the temperature too low? The default is implicit; consider explicit `temperature=1` for content prompts.

This is a known failure mode tracked in `CLAUDE.md` under "What bad looks like."

### Spec-kit gets confused

If spec-kit's `.specify/` directory is in a weird state, re-initialize:

```bash
rm -rf .specify
specify init . --integration claude
```

If `specify` itself isn't on PATH (or is the wrong package), see the install step above — spec-kit must be installed from `git+https://github.com/github/spec-kit.git`, not from PyPI.

You'll lose any specs in `.specify/specs/`, so commit them first if they matter.

---

## File locations reference

| What | Where |
|---|---|
| Operator's input briefs | Outside the repo (your home dir, your other project) |
| Generated bundles | `examples/generated-companies/<slug>/` (gitignored by default) |
| Reference companies | Not bundled — download from [paperclip.community/companies](https://paperclip.community/companies) (removed per ADR-011) |
| Prompts | `src/paperclip_blueprints/prompts/*.md` |
| Templates | `src/paperclip_blueprints/templates/*.j2` |
| Patterns | `src/paperclip_blueprints/patterns/*.py` |
| ADRs | `docs/adr/NNN-name.md` |
| Deployment gaps doc | `docs/deployment-gaps.md` |
| This file | `SETUP.md` |

---

## Updating this file

Update when:
- A new install step is added or removed
- A CLI subcommand changes its arguments
- Troubleshooting reveals a new common failure mode

Don't update for:
- Phase-internal changes (those go in CLAUDE.md / MASTER_PROMPTS.md)
- New ADRs (those live in `docs/adr/`)
