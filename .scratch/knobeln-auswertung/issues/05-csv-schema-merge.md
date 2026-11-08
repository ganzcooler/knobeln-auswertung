# 05 — CSV-Schema, atomisches Schreiben und Merge

Status: resolved
Blocked by: 01, 02

## Ziel

Die eine `auswertung.csv` lesen, neue Spieler/Durchgänge anhängen, Duplikate/Konflikte erkennen und abgeleitete Spalten neu berechnen, ohne bestehende Inhalte oder menschliche Korrekturen zu überschreiben.

## Aufgaben

- `io/csv_store.py`: CSV mit UTF-8 BOM, Semikolon und Standard-Quoting lesen/schreiben; eine Kopfzeile; leere Werte leer lassen.
- Schema-Migration: fehlende bekannte Spalten leer ergänzen; unbekannte Spalten beibehalten; bekannte Spalten nicht umbenennen.
- Merge nach Spec §9:
  - Index `(Bogen_ID, Spieler_Position, Wurf_Nr)` und `(Durchgang_Nr, Spieler_Nr)`.
  - Neuer Schlüssel → zwölf Zeilen anhängen.
  - Gleicher Schlüssel + identische Werte → Duplikat überspringen.
  - Gleicher Schlüssel + abweichende Werte → `Konflikt=ja`, `Status=konflikt`, `Konflikt_Detail` mit den Unterschieden, nichts überschreiben.
  - Menschliche Korrektur (`Punkte` != normalisiertes `Punkte_Roh`) erkennen und erhalten.
  - `Geprueft=ja` respektieren; neue abweichende Scans öffnen den Konflikt wieder.
  - Namens-Kanonisierung und `name_konflikt`.
  - Unleserliche Bögen als Platzhalterzeile.
- Abgeleitete Spalten für alle Gruppen neu berechnen: `Summe_Berechnet`, `Delta`, `Status`, `Warnung`, `Konflikt`.
- Atomisches Schreiben (Temp + Replace); Lock-/Permission-Fehler klar melden; optional `--backup` nach `auswertung.csv.bak`.
- Tests für alle Merge-Fälle.

## Abnahmekriterien

- Zwei Läufe mit demselben Scan erzeugen keine doppelten Zeilen.
- Ein neuer Scan mit gleichem `(Durchgang_Nr, Spieler_Nr)` und anderen Werten überschreibt nichts und erzeugt eine Konfliktwarnung.
- Eine manuell korrigierte `Punkte`-Zelle bleibt über weitere Läufe erhalten.
- `Geprueft=ja` verhindert erneutes Öffnen desselben Konflikts.
- `Summe_Berechnet`, `Delta`, `Status`, `Warnung` werden nach einer Korrektur neu berechnet.
- Die CSV bleibt bei einem Schreibfehler unverändert.

## Referenzen

- `../spec.md` §8, §9
- `../../docs/adr/0001-csv-as-state.md`
