# 06 — Orchestrierung, Zusammenfassung, Exit-Codes

Status: resolved
Blocked by: 03, 04, 05

## Ziel

Die Teile zu einem CLI-Lauf verbinden: Eingang → LLM → Validierung → Merge → CSV-Schreiben → Aufräumen → Zusammenfassung.

## Aufgaben

- `pipeline.py`: Verarbeitung aller Eingangsdateien, pro Seite LLM-Aufruf, Validierung, Merge in die bestehende CSV, atomisches Schreiben, anschließendes Aufräumen.
- Bekannte `Bogen_ID`s ohne `--reprocess` überspringen (Crash-Wiederaufnahme).
- Zusammenfassung: gelesene Dateien, neue Spieler, Duplikate, Konflikte, Warnungen, unleserliche Bögen, gelöscht/verschoben/behalten, Token und geschätzte Kosten.
- Exit-Codes:
  - `0`: alles sauber oder alle Warnungen mit `Geprueft=ja` bestätigt.
  - `2`: CSV geschrieben, aber offene Prüfpunkte oder Dateien im Eingang behalten.
  - `1`: fataler Fehler, keine CSV-Änderung und kein Aufräumen.
- Fehlerfälle: fehlender API-Key, API nicht erreichbar, ungültiges JSON, CSV gesperrt, unbekanntes Modell, nicht unterstützte Datei.
- `--reset`: bestehende CSV nach Rückfrage nach `auswertung.<timestamp>.bak.csv` verschieben und neu beginnen; ohne `--yes` nicht löschen.

## Abnahmekriterien

- Ein Lauf mit Fake-LLM verarbeitet mehrere Dateien und schreibt eine korrekte CSV.
- Ein technischer Fehler bei einer Datei stoppt die anderen nicht; die fehlerhafte Datei bleibt im Eingang, Exit 2.
- Ein CSV-Schreibfehler führt zu Exit 1 und lässt alle Eingabedateien unangetastet.
- `--reset` archiviert die alte CSV und beginnt leer.
- Die Zusammenfassung nennt alle relevanten Zähler.

## Referenzen

- `../spec.md` §5, §11
