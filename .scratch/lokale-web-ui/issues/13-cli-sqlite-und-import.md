# 13: CLI auf SQLite und Import umstellen

**Spec:** [../spec.md](../spec.md)

**What to build:** Die CLI wird auf SQLite und die Web-App umgestellt. `knobeln` startet die Web-UI, `knobeln web` ist ein Alias, und `knobeln import [PFAD]` importiert Scans aus einem Ordner ins Scan-Archiv und in dieselbe Datenbank. Die alten CSV-Optionen entfallen.

**Blocked by:** 01 — Turnier anlegen und lokale Web-App starten; 03 — Scans importieren und im Stapel sehen; 04 — Scan wird gelesen: Hintergrund-Extraktion

**Status:** resolved

- [x] `knobeln` ohne Argument startet die Web-UI; `knobeln web` startet denselben Server.
- [x] `knobeln import [PFAD]` importiert JPG, PNG und PDF aus einem Ordner ins Scan-Archiv und in die Datenbank.
- [x] `--db` und `--scans` überschreiben die Standardpfade.
- [x] `--model`, `--reasoning`, `--max-cost` und `--verbose` bleiben nutzbar.
- [x] Die alten CSV-Optionen (`--output`, `--review`, `--reset`, `--keep-input`) sind entfernt.
- [x] CLI und Web-UI sehen denselben Zustand in derselben SQLite-Datenbank.
- [x] Tests decken Web-Start, Import, Pfadoptionen und die gemeinsame Datenbank ab.
