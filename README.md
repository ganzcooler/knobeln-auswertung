# Knobeln-Auswertung

CLI zur Auswertung gescannter Knobeln-Protokollbögen. Ein Vision-LLM liest die
handgeschriebenen Punkte, die App prüft sie gegen die gedruckte Wertung und
pflegt eine einzige Excel-pivotfähige CSV. Die selbst gerechnete Summenzeile
ist eine Kontrolle: Abweichungen werden markiert, nie automatisch korrigiert.

## Installation

Voraussetzung: Python 3.13 und [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
# OPENROUTER_API_KEY in .env eintragen
```

Standardmodell ist `deepseek/deepseek-v4.1-flash` mit maximalem Reasoning.

## Benutzung

Neue Scans in `input/` legen (JPG, PNG oder PDF) und ausführen:

```bash
uv run knobeln
```

Ablauf:

1. Alle Dateien in `input/` werden gelesen.
2. Jede Seite wird als ein Bogen ausgewertet.
3. Die Ergebnisse werden in `auswertung.csv` gemerged.
4. Saubere Scans werden gelöscht.
5. Auffällige Scans (Summenabweichung, ungültige/fehlende Werte, Konflikt,
   unleserlich) werden nach `review/` verschoben.
6. Technisch fehlgeschlagene Dateien bleiben in `input/` für den nächsten Lauf.

Für eine neue Veranstaltung `--reset` verwenden (archiviert die alte CSV) oder
eine andere `--output`-Datei angeben.

Wichtige Optionen:

```text
--input PATH        Eingangsordner (Default: input)
--output PATH       CSV-Datei (Default: auswertung.csv)
--review PATH       Review-Ordner (Default: review)
--model MODEL       OpenRouter-Modell
--reasoning EFFORT  Reasoning-Effort (Default: max)
--reset             Neue Veranstaltung: bestehende CSV archivieren
--reprocess         Bekannte Bogen_IDs erneut lesen (umgeht auch den Cache)
--no-cache          LLM-Cache umgehen
--keep-input        Eingang nicht aufräumen (Debugging)
--dry-run           Nicht schreiben und nicht aufräumen
--backup            Vor dem Schreiben auswertung.csv.bak anlegen
--verbose           Ausführliche Ausgabe
--version           Version anzeigen
```

Exit-Codes: `0` sauber, `2` offene Prüfpunkte oder Dateien behalten,
`1` fataler Fehler (z. B. CSV gesperrt, API-Key fehlt).

## CSV und Pivot in Excel

Die CSV ist UTF-8 mit BOM und wird mit Semikolon geschrieben. Beim Einlesen
wird auch ein komma-getrennter Excel-Zwischenstand erkannt. In Excel:

1. **Daten → Aus Text/CSV** wählen, Datei `auswertung.csv` importieren.
2. Trennzeichen `;`, Kodierung UTF-8, erste Zeile als Kopfzeile.
3. Pivot erstellen: Zeilen = `Spieler_Nr` (optional `Spieler_Name`),
   Spalten = `Durchgang_Nr`, Werte = Summe von `Punkte`.

Die CSV ist die dauerhafte Quelle. Excel beobachtet sie nicht von selbst:
Nach jedem App-Lauf **Alle aktualisieren** klicken (oder ein Refresh-Intervall
setzen). Vor dem App-Lauf die CSV in Excel schließen, sonst kann Windows die
Datei sperren.

## Korrigieren

- `Punkte` ist die Spalte, die in die Pivot eingeht. Fehlerhafte Werte dort
  direkt korrigieren.
- `Summe_Bogen` ist die gelesene Summenzeile; bei Bedarf ebenfalls korrigieren.
- `Punkte_Roh` und `Summe_Bogen_Roh` sind die rohen LLM-Lesungen. Nicht
  bearbeiten, sie dienen der Nachvollziehbarkeit.
- `Korrektur` wird von der App gefüllt (z. B. `8.5 -> 85`).
- `Geprueft=ja` setzen, wenn ein Konflikt angesehen wurde und der bestehende
  Wert bleiben soll. Sonst öffnet die App denselben Konflikt beim nächsten Lauf
  erneut.
- `Kommentar` ist für eigene Notizen und bleibt pro Zeile erhalten.
- Gruppenfelder (`Summe_Bogen`, `Spieler_Name`, `Geprueft`) stehen auf allen
  zwölf Zeilen eines Spielers; die App liest den ersten nicht-leeren Wert. Am
  einfachsten die erste Zeile (`Wurf_Nr=1`) ändern oder den Wert in Excel nach
  unten füllen.
- `Namenskonflikt` wird von der App gefüllt. Nach Korrektur der Namen die
  Spalte leeren oder `Geprueft=ja` setzen.
- Nach der Korrektur `uv run knobeln` erneut ausführen (auch ohne neue Scans):
  Die abgeleiteten Spalten `Summe_Berechnet`, `Delta`, `Status` und `Warnung`
  werden neu berechnet.
- Ein unleserlicher Bogen bleibt als `bogen_unklar`-Zeile in der CSV. Wenn du
  denselben Scan erneut lesen willst, die Datei aus `review/` zurück nach
  `input/` legen und `--reprocess` verwenden. Bei einem neuen Scan mit anderer
  Datei die alte Platzhalterzeile in der CSV löschen.

## Spalten

| Spalte | Bedeutung |
| --- | --- |
| `Bogen_ID` | Hash der Quelle + Seite |
| `Quelle` | ursprünglicher Pfad im Eingang |
| `Seite` | Seite der Quelle |
| `Spieler_Position` | Spalte auf dem Bogen (1–4) |
| `Durchgang_Nr` | Durchgang 1–5 |
| `Spieler_Nr` | Spieler-Nummer |
| `Spieler_Name` | optionaler Name |
| `Wurf_Nr` | Zeile 1–12 |
| `Punkte` | finaler Punktwert (Pivot-Wert) |
| `Punkte_Roh` | rohe LLM-Lesung |
| `Korrektur` | App-Notiz zur Normalisierung |
| `Summe_Bogen_Roh` | rohe LLM-Lesung der Summenzeile |
| `Summe_Bogen` | gelesene/korrigierte Summenzeile |
| `Summe_Berechnet` | Summe der zwölf `Punkte` |
| `Delta` | `Summe_Bogen - Summe_Berechnet` |
| `Status` | Status-Codes, mehrere mit \| getrennt |
| `Warnung` | Klartext-Warnung |
| `Konflikt` | `ja`/`nein` |
| `Konflikt_Detail` | Unterschiede des Konflikts |
| `Namenskonflikt` | konkurrierende Namen (z. B. `A \| B`) |
| `Geprueft` | `ja`/`nein` |
| `Kommentar` | freie Notiz pro Zeile |

## Status-Codes

`ok`, `bogen_unklar`, `durchgang_unklar`, `spieler_unklar`, `spieler_doppelt`,
`wert_fehlt`, `wert_ungueltig`, `wert_korrigiert`, `summe_fehlt`,
`summe_ungueltig`, `summe_unvollstaendig`, `summe_abweichung`,
`summe_korrigiert`, `name_konflikt`, `konflikt`, `identitaet_konflikt`,
`geprueft`.

## Gültige Punktwerte

Die gedruckte Wertung ist maßgeblich und für das gesamte Spiel konstant:

```text
0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75,
80, 85, 90, 95, 100, 105, 110, 120, 130, 140, 150, 160, 170, 200
```

`0` gilt für `/` oder eine geschriebene 0. Leere Zellen sind fehlend.
Trennzeichen-Artefakte wie `8.5` werden zu 85 normalisiert; es wird nicht
gerundet und nicht geklemmt. Die `*`-Markierung der Wertung spielt für die
Auswertung keine Rolle.

## Entwicklung

```bash
uv run pytest
```

Die Tests nutzen einen Fake-LLM-Client und die Beispiele aus `examples/`.
Der echte Modell-Smoke-Test läuft erst, wenn `OPENROUTER_API_KEY` in `.env`
liegt.

## Dokumentation

- [`GLOSSARY.md`](GLOSSARY.md) — Begriffe
- [`docs/adr/`](docs/adr/) — Architekturentscheidungen
- [`.scratch/knobeln-auswertung/spec.md`](.scratch/knobeln-auswertung/spec.md) — Spezifikation
- [`.scratch/knobeln-auswertung/issues/`](.scratch/knobeln-auswertung/issues/) — Umsetzungstickets
