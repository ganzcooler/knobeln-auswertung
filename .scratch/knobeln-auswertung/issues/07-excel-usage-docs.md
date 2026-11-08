# 07 — Excel-Nutzung und README

Status: resolved
Blocked by: 05, 06

## Ziel

Eine kurze, vollständige Anleitung, mit der ein Mensch von der Installation bis zur Pivot in Excel kommt und die Korrektur-/Konfliktspalten richtig benutzt.

## Aufgaben

- `README.md` mit:
  - Installation über `uv`.
  - `.env` mit `OPENROUTER_API_KEY`.
  - CLI-Aufruf und Optionen.
  - Eingang `input/`, Review-Ordner, Lösch-/Verschiebeverhalten.
  - Excel-Import: Daten → Aus Text/CSV, Trennzeichen `;`, UTF-8, Kopfzeile.
  - Pivot: Zeilen = `Spieler_Nr`, Spalten = `Durchgang_Nr`, Werte = Summe `Punkte`.
  - Refresh nach jedem Lauf; CSV vorher in Excel schließen.
  - Korrektur-Workflow: `Punkte` bzw. `Summe_Bogen` korrigieren, `Geprueft=ja` für bestätigte Konflikte, `Kommentar` für Notizen.
  - Erklärung von `Status`, `Warnung`, `Konflikt`, `Geprueft`.
- Hinweis, dass Excel die Datei nicht von selbst beobachtet; optional Refresh-Intervall.
- Hinweis, dass `Punkte_Roh` und `Korrektur` App-Spalten sind und nicht bearbeitet werden sollten.

## Abnahmekriterien

- Ein neuer Nutzer kann mit der README die drei Beispielbögen verarbeiten und eine Pivot bauen.
- Die Anleitung widerspricht nicht der Spec.
- Die Korrektur- und Konfliktschritte sind eindeutig.

## Referenzen

- `../spec.md` §8.3, §11
