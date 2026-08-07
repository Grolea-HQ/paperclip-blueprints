# SETUP.md — Installation and daily usage

This guide covers getting the paperclip-blueprints project running on a fresh machine and the daily workflow once it's set up.

> 📖 For a narrative walkthrough, see [How to use Paperclip Blueprints](https://www.grolea.com/insights/how-to-use-paperclip-blueprints).

---

## First-time installation

### Prerequisites

- Python 3.11 or newer (`python3 --version`)
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- An Anthropic API key with access to Claude Opus 4.8 and Sonnet 4.6

### Clone and bootstrap

```bash
git clone git@github.com:Grolea-HQ/paperclip-blueprints.git
cd paperclip-blueprints

# Set up Python environment
uv sync

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

### Generating a company bundle

```bash
# 1. Copy the input template
cp examples/input-template.md my-brief.md

# 2. Fill it in — see the template's inline guidance and the validation checklist
# Pay particular attention to:
# - North star must be a measurable persistent outcome, not a task
# - "We are not" needs at least 2 entries (anti-drift framing)
# - Constraints are non-negotiable rules, not soft preferences

# 3. Generate
uv run blueprints generate --input my-brief.md --output examples/generated-companies/my-company/

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
uv run blueprints generate --input my-brief.md --output my-test/ --single-agent
```

### Validating an input without generating

```bash
uv run blueprints validate --input my-brief.md
```

This runs the input through Pydantic schemas and the goal-as-outcome / span-of-control rules without making any Anthropic API calls. Use it for fast iteration on the brief.

### Previewing only COMPANY.md (fail-fast)

```bash
uv run blueprints preview --input my-brief.md
```

Generates only the COMPANY.md content. ~30 seconds, one Opus call. Useful for iterating on identity content before paying for a full bundle generation.

### Checking a bundle's operating-canon coverage

```bash
uv run blueprints check-canon --input my-brief.md --bundle examples/generated-companies/my-company/
```

Checks whether the rules stated in the brief's section 11 reached an **already-rendered** bundle on disk. No generation, no API call, no API key required — so it is free to re-run as often as you like.

It prints the canon items it found in the brief, then one line per item that fell short: **missing** (in no generated file), **thin** (in exactly one, which it names), or **coverage unknown** (the item is named by a sentence rather than a phrase, so it cannot be searched for). Items carried by two or more files produce no output.

The same check runs automatically at the end of every `generate`, so these warnings also appear there. They are advisory — they never fail a run — and they report *reach*, not quality: whether a rule landed as usable procedure is yours to judge by reading the bundle.

`--bundle` must point at a rendered bundle directory (one containing `COMPANY.md` or `.paperclip.yaml`). An empty or non-bundle path is rejected rather than silently scanning the wrong tree.

### What else the brief controls

- **Section 11 — operating canon.** Threaded whole into the generators that write procedure, and encoded rather than summarised (ADR-037). How you mark it up determines what the coverage check can verify; `examples/input-template.md` documents the convention.
- **Section 12 — run-policy overrides.** Per-agent turn caps, concurrent-run limits, and heartbeat on/off, overriding the role-derived defaults (ADR-034). Blank keeps the defaults.
- **Routine scheduling.** The brief states cadence, not clock time. Each routine's time of day is derived deterministically from its task slug, so the same brief always yields the same schedule; remaining trigger collisions and out-of-order producer/consumer pairs are reported as warnings (ADR-036).
- **Section 9 — routine timezone.** An optional IANA zone name (e.g. `Europe/Helsinki`) that every routine is scheduled in; blank means UTC (ADR-038). Since routine times are spread across a working-day window, this is what makes that window *your* working day. An unrecognised zone name is rejected before generation starts.

---

## Troubleshooting

### `uv sync` fails on first install

Verify Python 3.11+. uv resolves against the version in `pyproject.toml`; older Python versions will fail at resolve time.

### Anthropic API calls fail with 401

Check `ANTHROPIC_API_KEY` is set in `.env` and that the key has access to both `claude-opus-4-8` and `claude-sonnet-4-6` models. Most Anthropic keys do; if yours doesn't, check the Console.

### Generated bundle fails Paperclip import

Every bundle is validated against the `paperclip/v1` and `agentcompanies/v1` schemas
**before** it is written to disk (Constitution II), so a bundle that exists on disk has
already passed the in-stack validators. There is no separate re-validation subcommand.

- If `generate` itself fails validation, it writes the **rejected** bundle to
  `<output>-failed/` and prints the violations — inspect that directory to see what the
  validators caught.
- If a written bundle passed here but still fails at Paperclip import, the import format
  may have changed — check the Paperclip docs and update
  `src/paperclip_blueprints/validators/`.

### Re-importing duplicates agents/projects

Import each bundle into a **fresh** target — e.g. `companies.sh add --target new
--include company,agents,projects,tasks,skills`. Importing a bundle over an existing
company uses Paperclip's default collision strategy, which silently duplicates
entities (`-2`-suffixed agents and projects) rather than updating them. On the
generation side, `blueprints generate` refuses a non-empty `--output` directory
unless `--force` is passed; `--force` cleanly replaces the directory (it never unions
two generations).

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
| This file | `SETUP.md` |

---

## Updating this file

Update when:
- A new install step is added or removed
- A CLI subcommand changes its arguments
- Troubleshooting reveals a new common failure mode

Don't update for:
- New ADRs (those live in `docs/adr/`)
