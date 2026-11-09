"""CLI-Einstiegspunkt: Web-UI primär, Batch-Lauf als Zweitweg."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .config import ConfigError, build_config
from .llm.cache import LLMCache
from .llm.client import OpenRouterClient
from .pipeline import Pipeline, PipelineError, RunSummary
from .web.server import run_server

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
    help="Lokale Web-UI und Batch-Auswertung für Knobeln-Protokollbögen.",
)
console = Console(stderr=True)


@app.callback()
def main(ctx: typer.Context, version: bool = typer.Option(False, "--version")) -> None:
    if version:
        console.print(f"knobeln-auswertung {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        run_server()
        raise typer.Exit()


@app.command()
def web(
    db: Path | None = typer.Option(
        None, "--db", help="SQLite-Datei (Default: knobeln.db)"
    ),
    port: int = typer.Option(8000, "--port", help="Port der lokalen Web-UI"),
) -> None:
    """Startet die lokale Web-UI."""
    run_server(db, port=port)
    raise typer.Exit()


@app.command()
def run(
    input_dir: Path | None = typer.Option(
        None, "--input", help="Eingangsordner (Default: input)"
    ),
    output_csv: Path | None = typer.Option(
        None, "--output", help="CSV-Datei (Default: auswertung.csv)"
    ),
    review_dir: Path | None = typer.Option(
        None, "--review", help="Review-Ordner (Default: review)"
    ),
    model: str | None = typer.Option(None, "--model", help="OpenRouter-Modell"),
    reasoning: str | None = typer.Option(
        None, "--reasoning", help="Reasoning-Effort (Default: max)"
    ),
    reset: bool = typer.Option(
        False, "--reset", help="Neue Veranstaltung: bestehende CSV archivieren"
    ),
    yes: bool = typer.Option(False, "--yes", help="Rückfragen automatisch bestätigen"),
    reprocess: bool = typer.Option(
        False, "--reprocess", help="Bekannte Bogen_IDs erneut lesen"
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="LLM-Cache umgehen"),
    keep_input: bool = typer.Option(
        False, "--keep-input", help="Eingang nicht aufräumen"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Nicht schreiben und nicht aufräumen"
    ),
    backup: bool = typer.Option(
        False, "--backup", help="Vor dem Schreiben eine .bak-Kopie anlegen"
    ),
    max_cost: float | None = typer.Option(
        None,
        "--max-cost",
        help="Kostenlimit in USD pro Lauf; bricht vor dem CSV-Schreiben ab",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Ausführliche Ausgabe"),
) -> None:
    """Wertet Scans als CSV aus (alter Batch-Pfad)."""
    if reset and not yes:
        if not typer.confirm("Bestehende CSV wirklich archivieren und neu beginnen?"):
            reset = False

    try:
        config = build_config(
            input_dir=input_dir,
            output_csv=output_csv,
            review_dir=review_dir,
            model=model,
            reasoning=reasoning,
            reset=reset,
            reprocess=reprocess,
            no_cache=no_cache,
            keep_input=keep_input,
            dry_run=dry_run,
            verbose=verbose,
            backup=backup,
            max_cost=max_cost,
        )
        api_key = config.require_api_key()
    except ConfigError as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from exc

    client = OpenRouterClient(
        api_key=api_key,
        model=config.model,
        reasoning=config.reasoning,
        cache=LLMCache(config.cache_dir),
        no_cache=config.no_cache or config.reprocess,
    )

    log = (lambda msg: console.print(f"[dim]{msg}[/dim]")) if verbose else None
    pipeline = Pipeline(config, client, log=log)
    try:
        summary = pipeline.run()
    except PipelineError as exc:
        console.print(f"[red]Fehler:[/red] {exc}")
        raise typer.Exit(1) from exc

    _print_summary(summary, config)
    raise typer.Exit(summary.exit_code)


def _print_summary(summary: RunSummary, config) -> None:
    console.print()
    console.print("[bold]Zusammenfassung[/bold]")
    console.print(
        f"Dateien: {summary.files_total} "
        f"(verarbeitet {summary.files_processed}, "
        f"übersprungen {summary.files_skipped})"
    )
    console.print(
        f"Seiten gelesen: {summary.pages_processed}; "
        f"neue Spielergruppen: {summary.new_groups}; "
        f"Duplikate: {summary.duplicates}; "
        f"Konflikte: {summary.conflicts}"
    )
    console.print(
        f"Offene Prüfpunkte: {summary.open_groups}; unleserlich: {summary.unreadable}"
    )
    console.print(
        f"Eingang: {summary.deleted} gelöscht, "
        f"{summary.moved} nach review, {summary.kept} behalten"
    )
    if summary.prompt_tokens or summary.completion_tokens or summary.cache_hits:
        console.print(
            f"Tokens: {summary.prompt_tokens} prompt / "
            f"{summary.completion_tokens} completion "
            f"({summary.reasoning_tokens} reasoning), "
            f"ca. ${summary.cost_usd:.4f}; "
            f"Cache-Treffer: {summary.cache_hits}"
        )
        if summary.file_costs:
            console.print("Kosten pro Datei:")
            for file_cost in summary.file_costs:
                cache = " (Cache)" if file_cost.cached else ""
                console.print(
                    f"  {file_cost.quelle}: "
                    f"{file_cost.prompt_tokens}/{file_cost.completion_tokens} "
                    f"Tokens, ca. ${file_cost.cost_usd:.4f}{cache}"
                )
    console.print(f"CSV: {config.output_csv}")

    if summary.warnings:
        console.print()
        console.print("[yellow]Hinweise:[/yellow]")
        for warning in summary.warnings:
            console.print(f"  - {warning}")

    if summary.cleanup_failures:
        console.print()
        console.print("[red]Aufräumen fehlgeschlagen:[/red]")
        for failure in summary.cleanup_failures:
            console.print(f"  - {failure}")


if __name__ == "__main__":
    app()
