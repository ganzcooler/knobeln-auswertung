# 04 — Eingang, PDF-Verarbeitung und Aufräumen

Status: resolved
Blocked by: 01

## Ziel

Alle neuen Scans aus `input/` zuverlässig einsammeln, PDFs in Seiten zerlegen und nach erfolgreichem CSV-Schreiben sauber löschen bzw. nach `review/` verschieben.

## Aufgaben

- `io/input_scanner.py`: rekursiv `.jpg`, `.jpeg`, `.png`, `.pdf` finden; sortiert; versteckte Dateien ignorieren; nicht unterstützte Dateien melden und liegen lassen.
- `io/pdf.py`: PDFs mit `pypdfium2` rendern (300 DPI), Seitenzahl und `Bogen_ID` = Datei-Hash + Seite.
- `Bogen_ID`-Berechnung für Einzelbilder: Datei-Hash + Seite 1.
- `io/cleanup.py`:
  - saubere Dateien löschen,
  - auffällige Dateien (`Status != ok`, `Konflikt=ja`, `bogen_unklar`) nach `review/` verschieben,
  - technische Fehler in `input/` lassen,
  - relative Pfade im Review-Ordner erhalten, Namenskollisionen mit Hash-Suffix auflösen,
  - mehrseitige PDFs erst entfernen, wenn alle Seiten verarbeitet sind.
- Aufräumen strikt nach erfolgreichem CSV-Schreiben; bei Fehler nichts löschen/verschieben.
- `--keep-input`, `--dry-run`, `--reprocess` berücksichtigen.

## Abnahmekriterien

- Ein sauberer Scan verschwindet aus `input/`.
- Ein auffälliger Scan liegt nach dem Lauf in `review/` und nicht mehr in `input/`.
- Ein technisch fehlgeschlagener Scan bleibt in `input/`.
- Ein mehrseitiges PDF bleibt in `input/`, wenn eine Seite technisch fehlschlägt; bereits erfolgreiche Seiten werden beim nächsten Lauf übersprungen.
- Bei gesperrter/fehlgeschlagener CSV wird keine Eingabedatei angefasst.
- Tests nutzen temporäre Verzeichnisse.

## Referenzen

- `../spec.md` §4, §10
