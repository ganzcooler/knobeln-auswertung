# Knobeln-Auswertung

Lokale Web-App zur Auswertung gescannter Knobeln-Protokollbögen. Ein Vision-LLM
liest die handgeschriebenen Punkte, die App prüft sie gegen die gedruckte
Wertung und führt die Turnierleitung durch **Scannen → Prüfen → Rangliste**.
Die selbst gerechnete Summenzeile bleibt bei gescannten Bögen eine Kontrolle:
Abweichungen werden markiert, nie automatisch korrigiert.

Die App läuft nur auf `127.0.0.1`. SQLite ist der Zustand; Original-Scans liegen
dauerhaft im Scan-Archiv. Eine CSV gibt es nicht mehr. Wenn am Veranstaltungstag
die LLM-Verbindung fehlt, können die Summen pro Spieler und Durchgang manuell
erfasst werden.

## Installation

Voraussetzung: Python 3.13 und [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
# OPENROUTER_API_KEY in .env eintragen (nur für die Extraktion nötig)
```

Standardmodell ist `deepseek/deepseek-v4.1-flash` mit maximalem Reasoning.

## Start

```bash
uv run knobeln
```

Öffnet die lokale Web-UI auf <http://127.0.0.1:8000>. `uv run knobeln web` ist
der explizite Alias.

Optionen:

```text
--db PATH       SQLite-Datei (Default: knobeln.db)
--scans PATH    Scan-Archiv (Default: data/scans)
--port PORT     Port der lokalen Web-UI (Default: 8000)
```

Die App startet auch ohne API-Key und ohne Internet. Nur die Extraktion wartet
dann; Prüfen, manuelle Erfassung, Rangliste und XLSX-Export funktionieren
vollständig lokal.

## Ablauf

1. **Turnier und Durchgang** anlegen. Ein Turnier enthält die Durchgänge 1–5.
2. **Scannen:** JPG, PNG oder PDF per Drag-and-drop oder Dateiauswahl ablegen.
   Die Originale bleiben im Scan-Archiv; die Extraktion läuft als
   Hintergrundjob. Duplikate werden erkannt.
3. **Prüfen:** Die Queue zeigt nur die Fälle, die eine Entscheidung brauchen:
   Summenfehler, unzulässige oder fehlende Werte, unklare Ziffern, Konflikte
   und Kopfzeilen. Der Scan bleibt neben den Werten sichtbar.
4. **Manuell erfassen:** Fehlt die LLM-Verbindung, reicht pro Spieler und
   Durchgang eine Summe. Manuelle Ergebnisse sind sichtbar als „manuell“
   markiert und zählen für Rangliste und Abschluss.
5. **Rangliste:** Durchgang und Gesamt, geteilter Rang bei Gleichstand,
   Vollbild für den Beamer und XLSX-Export.
6. **Durchgang abschließen:** Nur ohne offene Prüffälle. Der Durchgang wird
   gesperrt und kann mit Bestätigung wieder geöffnet werden.

## Batch-Import

```bash
uv run knobeln import ./scans --turnier "Sommerfest 2026" --durchgang 1
```

Der Import legt Turnier und Durchgang bei Bedarf an, kopiert die Scans ins
Archiv und verarbeitet sie mit demselben Anwendungskern wie die Web-UI.
`--model`, `--reasoning`, `--max-cost`, `--db` und `--scans` werden unterstützt.

## Daten

- **SQLite:** `knobeln.db` (per `--db` änderbar) ist der einzige Zustand.
- **Scan-Archiv:** `data/scans/` (per `--scans` änderbar); Dateien werden nach
  der Verarbeitung nicht gelöscht.
- **Sicherung:** Vor dem Löschen eines Turniers oder dem Wiederöffnen eines
  Durchgangs legt die App eine SQLite-Kopie an.
- Alte `auswertung.csv`-Daten und der frühere `review/`-Ordner werden nicht
  importiert.

## Entwicklung

```bash
uv sync --group dev
uv run pre-commit install

./scripts/check.sh       # Ruff, Format, Pyright, Pytest
./scripts/doctor.sh      # uv, .env, Git-Remote, Scratch-Verzeichnis
```

Die Tests nutzen einen Fake-LLM-Client und die Beispiele aus `examples/`.
Der echte Modelltest ist kostenpflichtig und läuft nur manuell:

```bash
uv run pytest --run-manual
```

## Dokumentation

- [`GLOSSARY.md`](GLOSSARY.md) — Begriffe
- [`docs/adr/`](docs/adr/) — Architekturentscheidungen
- [`.scratch/lokale-web-ui/spec.md`](.scratch/lokale-web-ui/spec.md) — Spezifikation
- [`.scratch/lokale-web-ui/issues/`](.scratch/lokale-web-ui/issues/) — Umsetzungstickets
