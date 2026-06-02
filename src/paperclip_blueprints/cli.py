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
from .models.input import BriefValidationError, parse_brief
from .renderers.bundle import BundleError, build_and_write
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
    """Parse and validate a brief file, raising typer.Exit(1) on failure."""
    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        typer.echo(f"error: cannot read {input_path}: {exc}", err=True)
        raise typer.Exit(1) from exc
    try:
        return parse_brief(text)
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
        None, "--model", help="Override the synthesis model (e.g. opus-4.7, sonnet-4.6)."
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Stream progress/thinking."),
    force: bool = typer.Option(False, "--force", help="Overwrite a non-empty output dir."),
) -> None:
    """Generate a company bundle from a brief.

    Default mode produces the full multi-agent bundle; ``--single-agent`` produces
    the minimal one-agent bundle (the size-one special case).
    """
    brief = _load_brief(input)
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
