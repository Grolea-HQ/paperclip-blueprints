"""Typer CLI for Paperclip Blueprints — `blueprints` binary.

Commands: ``generate`` (US1), ``validate`` (US2), ``preview`` (US3). Only
``generate --single-agent`` is wired in v0.1a's MVP; ``validate`` and ``preview``
are stubbed until their stories are implemented.
"""

from __future__ import annotations

from pathlib import Path

import typer

from .config import MissingAPIKeyError
from .generators.client import GenerationError, LLMClient
from .generators.identity import generate_identity
from .models.input import (
    BriefStructureError,
    BriefValidationError,
    parse_brief,
    slug_divergence_warning,
)
from .renderers.bundle import BundleError, build_and_write
from .renderers.canon import (
    canon_coverage,
    canon_warnings,
    extract_canon_terms,
    extraction_warnings,
)
from .renderers.render import render_company_md
from .validators import BundleValidationError

app = typer.Typer(
    help="Generate deployable Paperclip company bundles from a Markdown brief.",
    no_args_is_help=True,
    add_completion=False,
)


def _make_client() -> LLMClient:
    """Construct the real Anthropic-backed client. Patched in tests."""
    return LLMClient()


def _load_brief(input_path: Path):
    """Parse and validate a brief file, raising typer.Exit(1) on failure.

    The two failure classes are reported differently because they are different states. A
    structural failure means the sections do not line up, so no field error can be trusted;
    the message says which sections and says that fields were not examined.
    """
    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        typer.echo(f"error: cannot read {input_path}: {exc}", err=True)
        raise typer.Exit(1) from exc
    try:
        return parse_brief(text, warn=lambda message: typer.echo(f"warning: {message}", err=True))
    except BriefStructureError as exc:
        typer.echo("brief structure failed:", err=True)
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    except BriefValidationError as exc:
        typer.echo("brief validation failed:", err=True)
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command()
def generate(
    input: Path = typer.Option(..., "--input", help="Path to the company brief Markdown."),
    output: Path = typer.Option(..., "--output", help="Directory to write the bundle into."),
    single_agent: bool = typer.Option(
        False, "--single-agent", help="Generate a one-agent bundle (v0.1a)."
    ),
    model: str | None = typer.Option(
        None, "--model", help="Override the synthesis model (e.g. opus-4.8, sonnet-4.6)."
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Stream progress/thinking."),
    force: bool = typer.Option(False, "--force", help="Overwrite a non-empty output dir."),
) -> None:
    """Generate a company bundle from a brief.

    Default mode produces the full multi-agent bundle; ``--single-agent`` produces
    the minimal one-agent bundle (the size-one special case).
    """
    brief = _load_brief(input)
    if (warning := slug_divergence_warning(brief)) is not None:
        typer.echo(f"warning: {warning}", err=True)
    if verbose:
        kind = "single-agent" if single_agent else "multi-agent"
        typer.echo(f"brief OK: {brief.name} ({brief.slug}) — generating {kind} bundle", err=True)

    client = _make_client()
    try:
        dest = build_and_write(
            brief,
            output,
            client,
            single_agent=single_agent,
            model=model,
            force=force,
            progress=lambda msg: typer.echo(msg, err=True),
        )
    except BundleValidationError as exc:
        typer.echo(f"generation failed: {exc}", err=True)
        typer.echo(f"rejected bundle written to {output}-failed/ for inspection", err=True)
        raise typer.Exit(1) from exc
    except (GenerationError, BundleError, MissingAPIKeyError) as exc:
        typer.echo(f"generation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"✓ Bundle written to {dest}")
    _print_cost_summary(client, verbose=verbose)


def _print_cost_summary(client: LLMClient, *, verbose: bool) -> None:
    """Print the run's total token usage and estimated cost (US4, SC-011)."""
    summary = client.usage_summary()
    t = summary["total"]
    if t["calls"] == 0:
        return
    typer.echo(
        f"cost: {t['calls']} calls, {t['input_tokens']} in / {t['output_tokens']} out tokens "
        f"— est. ${t['cost_usd']:.4f}"
    )
    if verbose:
        for model_id, m in summary["by_model"].items():
            typer.echo(
                f"  {model_id}: {m['calls']} calls, "
                f"{m['input_tokens']}+{m['output_tokens']} tok, ${m['cost_usd']:.4f}",
                err=True,
            )


@app.command()
def validate(
    input: Path = typer.Option(..., "--input", help="Path to the company brief Markdown."),
) -> None:
    """Validate a brief against the input rules (no API calls)."""
    brief = _load_brief(input)
    typer.echo(f"brief OK: {brief.name} ({brief.slug})")


_BUNDLE_TEXT_SUFFIXES = frozenset({".md", ".yaml", ".yml", ".txt"})

_BUNDLE_MARKERS = ("COMPANY.md", ".paperclip.yaml")


def _resolve_bundle_dir(raw: str) -> Path:
    """Resolve a ``--bundle`` argument, refusing anything that is not a bundle.

    Two guards, because the failure they prevent is the one this whole feature exists to
    close: a check that confidently answers a *different question* than the one asked.

    ``Path("")`` evaluates to ``PosixPath(".")`` and passes ``is_dir()``, so an unset shell
    variable turns ``--bundle "$MY_BUNDLE"`` into a silent scan of the working directory —
    reporting real-looking coverage against the wrong tree. An empty path is therefore a
    hard error, never a fallback.

    A non-empty path pointing somewhere that is not a bundle fails the same way, so the
    directory must also carry a bundle marker at its root.

    The argument is taken as a raw ``str`` deliberately: converting to ``Path`` first
    erases the emptiness (``Path("")`` *is* ``PosixPath(".")``), so the guard has to run
    before the type conversion that hides what it is looking for.
    """
    if not raw.strip():
        typer.echo(
            "error: --bundle is empty. An empty path resolves to the current directory, "
            "which would scan the wrong tree and report coverage for it.",
            err=True,
        )
        raise typer.Exit(1)
    bundle = Path(raw)
    if not bundle.is_dir():
        typer.echo(f"error: --bundle {bundle} is not a directory", err=True)
        raise typer.Exit(1)
    if not any((bundle / marker).is_file() for marker in _BUNDLE_MARKERS):
        typer.echo(
            f"error: --bundle {bundle} does not look like a rendered bundle "
            f"(expected one of {', '.join(_BUNDLE_MARKERS)} at its root)",
            err=True,
        )
        raise typer.Exit(1)
    return bundle


def _load_rendered_bundle(bundle_dir: Path) -> dict[str, str]:
    """Read an already-rendered bundle directory into a path → content map."""
    files: dict[str, str] = {}
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _BUNDLE_TEXT_SUFFIXES:
            continue
        try:
            files[path.relative_to(bundle_dir).as_posix()] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return files


@app.command(name="check-canon")
def check_canon(
    input: Path = typer.Option(..., "--input", help="Path to the company brief Markdown."),
    bundle: str = typer.Option(
        ..., "--bundle", help="Directory of an already-rendered bundle to scan."
    ),
) -> None:
    """Check an existing bundle for the brief's section-11 operating canon (ADR-037).

    Runs extraction and coverage against a bundle already on disk. No generation, no API
    call, no API key — so the extraction thresholds can be calibrated against a real brief
    and a real bundle, and re-run after each adjustment, at zero cost.

    Reports reach only. Whether canon that IS present landed as usable procedure is a
    judgement this command does not make.
    """
    brief = _load_brief(input)
    if not brief.free_text:
        typer.echo("brief has no section-11 operating canon — nothing to check.")
        return
    bundle_dir = _resolve_bundle_dir(bundle)
    files = _load_rendered_bundle(bundle_dir)
    if not files:
        typer.echo(f"error: no readable text files under {bundle_dir}", err=True)
        raise typer.Exit(1)

    terms = extract_canon_terms(
        brief.free_text,
        exclude_texts=[
            brief.description,
            brief.north_star,
            brief.we_are,
            *brief.goals,
            *brief.we_are_not,
            *brief.constraints,
        ],
    )
    typer.echo(f"scanned {len(files)} files in {bundle_dir}")
    typer.echo(f"extracted {len(terms)} canon term(s) unique to section 11:")
    for term in terms:
        typer.echo(f"  - {term.text}")

    coverage = canon_coverage(terms, files)
    warnings = extraction_warnings(brief.free_text, terms) + canon_warnings(coverage)
    if warnings:
        typer.echo("")
        for message in warnings:
            typer.echo(f"warning: {message}", err=True)
    probed = [c for c in coverage if c.term.probeable]
    missing = sum(1 for c in probed if c.is_missing)
    thin = sum(1 for c in probed if c.is_thin)
    unprobeable = len(coverage) - len(probed)
    typer.echo("")
    summary = f"{len(probed) - missing - thin} carried, {thin} thin, {missing} missing"
    if unprobeable:
        summary += f", {unprobeable} not searchable"
    typer.echo(summary)


@app.command()
def preview(
    input: Path = typer.Option(..., "--input", help="Path to the company brief Markdown."),
    output: Path | None = typer.Option(
        None, "--output", help="Write COMPANY.md here instead of stdout."
    ),
    model: str | None = typer.Option(None, "--model", help="Override the synthesis model."),
    verbose: bool = typer.Option(False, "--verbose", help="Stream progress/thinking."),
) -> None:
    """Generate only the COMPANY.md identity document, to fail fast."""
    brief = _load_brief(input)
    if verbose:
        typer.echo(f"brief OK: {brief.name} ({brief.slug})", err=True)

    try:
        client = _make_client()
        company = generate_identity(brief, client, model=model)
    except (GenerationError, MissingAPIKeyError) as exc:
        typer.echo(f"preview failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    document = render_company_md(company)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
        typer.echo(f"identity written to {output}", err=True)
    else:
        typer.echo(document)


if __name__ == "__main__":
    app()
