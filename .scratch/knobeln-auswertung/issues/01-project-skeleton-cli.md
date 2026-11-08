# 01 — Projekt-Skeleton und CLI

Status: resolved
Blocked by: —

## Ziel

Ein lauffähiges Python-3.13-Projekt mit `uv`, `pyproject.toml`, Typer-CLI, Konfiguration und den nötigen Ordnern. Noch keine fachliche Pipeline.

## Aufgaben

- `pyproject.toml` mit Projektmetadaten, Abhängigkeiten (`openai`, `pydantic`, `python-dotenv`, `pypdfium2`, `Pillow`, `typer`, `rich`, `pytest`) und Console-Script `knobeln`.
- `src/knobeln/cli.py` mit den Optionen aus der Spec: `--input`, `--output`, `--review`, `--model`, `--reasoning`, `--reset`, `--reprocess`, `--no-cache`, `--keep-input`, `--dry-run`, `--verbose`, `--version`.
- `src/knobeln/config.py`: `.env` laden, Env-Variablen und CLI-Overrides zusammenführen.
- `.env.example` mit `OPENROUTER_API_KEY=`.
- `.gitignore`: `.env`, `input/*`, `review/*`, `auswertung.csv`, `*.bak.csv`, `.cache/`, `.venv/`, `__pycache__/`.
- `input/` und `review/` bei Bedarf anlegen.
- Fehlender API-Key: klare Meldung, Exit 1, bevor irgendetwas verarbeitet wird.

## Abnahmekriterien

- `uv run knobeln --help` zeigt alle Optionen.
- `uv run knobeln --version` funktioniert.
- Ohne `OPENROUTER_API_KEY` endet der Lauf mit Exit 1 und einer verständlichen Meldung.
- Konfigurationsreihenfolge CLI > Env > `.env` > Default ist getestet.

## Referenzen

- `../spec.md` §5, §12
