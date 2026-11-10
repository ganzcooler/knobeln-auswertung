"""CLI-Einstiegspunkt: Web-UI primär, Import als Batch-Zweitweg."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .io.input_scanner import SUPPORTED_SUFFIXES
from .runtime import build_service
from .web.server import run_server

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
    help="Lokale Web-UI und Batch-Import für Knobeln-Protokollbögen.",
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
    scans: Path | None = typer.Option(
        None, "--scans", help="Scan-Archiv (Default: data/scans)"
    ),
    port: int = typer.Option(8000, "--port", help="Port der lokalen Web-UI"),
    max_cost: float | None = typer.Option(
        None, "--max-cost", help="Kostenlimit in USD pro Lauf"
    ),
) -> None:
    """Startet die lokale Web-UI."""
    run_server(db, scan_dir=scans, port=port, max_cost=max_cost)
    raise typer.Exit()


@app.command("import")
def import_scans(
    pfad: Path | None = typer.Argument(
        None, help="Ordner mit JPG-, PNG- oder PDF-Scans (Default: input)"
    ),
    db: Path | None = typer.Option(
        None, "--db", help="SQLite-Datei (Default: knobeln.db)"
    ),
    scans: Path | None = typer.Option(
        None, "--scans", help="Scan-Archiv (Default: data/scans)"
    ),
    turnier: str = typer.Option("Import", "--turnier", help="Ziel-Turnier"),
    durchgang: int = typer.Option(1, "--durchgang", help="Ziel-Durchgang 1–5"),
    model: str | None = typer.Option(None, "--model", help="OpenRouter-Modell"),
    reasoning: str | None = typer.Option(
        None, "--reasoning", help="Reasoning-Effort (Default: low)"
    ),
    max_cost: float | None = typer.Option(
        None, "--max-cost", help="Kostenlimit in USD pro Lauf"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Ausführliche Ausgabe"),
) -> None:
    """Importiert Scans aus einem Ordner in das Scan-Archiv und die Datenbank."""
    pfad = pfad or Path("input")
    if not pfad.exists():
        console.print(f"[red]Fehler:[/red] Pfad nicht gefunden: {pfad}")
        raise typer.Exit(1)
    service = build_service(
        db_path=db,
        scan_dir=scans,
        max_cost=max_cost,
        model=model,
        reasoning=reasoning,
    )
    ziel = service.ensure_import_context(turnier, durchgang)
    dateien = sorted(
        path
        for path in pfad.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    importiert = 0
    fehler: list[str] = []
    for path in dateien:
        if verbose:
            console.print(f"[dim]importiere: {path}[/dim]")
        try:
            bogen = service.import_scan(
                dateiname=path.name,
                data=path.read_bytes(),
                durchgang_id=ziel.id,
            )
            importiert += len(bogen)
        except Exception as exc:  # noqa: BLE001 - Sammelreport statt Abbruch
            fehler.append(f"{path.name}: {exc}")
    verarbeitet = service.process_pending_jobs()
    console.print(
        f"Import: {importiert} Bogen in Turnier {turnier!r}, "
        f"Durchgang {durchgang}; {verarbeitet} gelesen."
    )
    if fehler:
        console.print("[yellow]Hinweise:[/yellow]")
        for eintrag in fehler:
            console.print(f"  - {eintrag}")
        raise typer.Exit(2)
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
