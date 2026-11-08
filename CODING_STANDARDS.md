# Coding Standards

Für den Review-Agenten. Mechanische Regeln prüfen Ruff, Pyright und Pre-commit; hier stehen nur fachliche Judgement Calls.

## Leitsätze

- **Fehlend ist nicht 0.** Eine leere Zelle bleibt `None`/`wert_fehlt`. Ein LLM-Kandidat füllt sie nicht heimlich; eine geschriebene `0` ist dagegen ein gültiger Wert.
- **Summe ist Kontrolle.** `Summe_Bogen` wird mit `Summe_Berechnet` verglichen, nie zur Korrektur von Zellwerten benutzt. Abweichungen werden markiert, nicht geglättet.
- **CSV ist Zustand.** Bestehende Inhalte, unbekannte Spalten und `Kommentar` pro Zeile bleiben erhalten. Änderungen an abgeleiteten Spalten sind erlaubt; Inhaltsspalten nie überschreiben.
- **Konflikt statt Überschreiben.** Gleicher `(Durchgang_Nr, Spieler_Nr)` mit abweichenden Werten erzeugt einen Konflikt. `Geprueft=ja` bestätigt; ein neuer abweichender Scan öffnet ihn wieder.
- **Gruppenfelder sind bewusst gruppenweit.** `Geprueft` und `Spieler_Name` gelten für alle zwölf Zeilen eines Spielers; `Kommentar` ist pro Zeile.
- **Externe Schema-Namen sind Verträge.** `llm/schema.py` ist der externe LLM-Vertrag. Interne Renames laufen über Aliase; `PROMPT_VERSION` steigt nur bei semantischen Prompt-/Schema-Änderungen.
- **Kosten und Secrets.** Token/Kosten pro Datei und gesamt loggen. API-Keys nie in Logs, CSV oder Commits; `.env` bleibt ignoriert.

## Domänenbegriffe

`Wurf-Nr.` ist die Zeile 1–12; `Wurf` ist die Würfelkombination der Wertungstabelle. Für die Zeilen heißt das Modell `WurfZeileLLM`, das Feld `wurf_zeilen`. `BogenRef` bündelt `(bogen_id, quelle, seite)`.
