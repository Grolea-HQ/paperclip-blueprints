"""Typer CLI for Paperclip Blueprints — `blueprints` binary.

Commands: ``generate`` (US1), ``validate`` (US2), ``preview`` (US3). Only
``generate --single-agent`` is wired in v0.1a's MVP; ``validate`` and ``preview``
are stubbed until their stories are implemented.
"""

from __future__ import annotations

from pathlib import Path

import typer

from .generators.client import GenerationError, LLMClient
from .models.input import BriefValidationError, parse_brief
from .renderers.bundle import BundleError, build_and_write

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
    """Generate a company bundle from a brief."""
    if not single_agent:
        typer.echo("error: v0.1a only supports --single-agent.", err=True)
        raise typer.Exit(1)

    brief = _load_brief(input)
    if verbose:
        typer.echo(f"brief OK: {brief.name} ({brief.slug})", err=True)

    try:
        client = _make_client()
        dest = build_and_write(brief, output, client, model=model, force=force)
    except (GenerationError, BundleError) as exc:
        typer.echo(f"generation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"bundle written to {dest}")


@app.command()
def validate(
    input: Path = typer.Option(..., "--input", help="Path to the company brief Markdown."),
) -> None:
    """Validate a brief against the input rules (no API calls)."""
    raise NotImplementedError("validate is wired in task T045 (US2)")


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
    raise NotImplementedError("preview is wired in task T047 (US3)")


if __name__ == "__main__":
    app()
