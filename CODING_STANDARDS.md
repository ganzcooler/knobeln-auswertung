# Coding Standards

Für den Review-Agenten. Mechanische Regeln prüfen Ruff, Pyright und Pre-commit; hier stehen nur fachliche Judgement Calls.

## Leitsätze

- **Fehlend ist nicht 0.** Eine leere Zelle bleibt `None`/`wert_fehlt`. Ein LLM-Kandidat füllt sie nicht heimlich; eine geschriebene `0` ist dagegen ein gültiger Wert.
- **Summe ist Kontrolle.** `Summe_Bogen` wird mit `Summe_Berechnet` verglichen, nie zur Korrektur von Zellwerten benutzt. Abweichungen werden markiert, nicht geglättet.
- **SQLite ist Zustand.** Gescannte Werte, Rohwerte, Korrekturhinweise und Kommentare bleiben erhalten; abgeleitete Status werden neu berechnet. Original-Scans werden nach der Verarbeitung nicht gelöscht.
- **Konflikt statt Überschreiben.** Gleicher `(Durchgang, Spieler-Nr.)` mit abweichenden Ergebnissen erzeugt einen Konflikt mit beiden Erfassungen. `Geprueft` bestätigt; ein neuer abweichender Scan öffnet ihn wieder.
- **Manuelle Ergebnisse sind eine sichtbare Ausnahme.** Nur bei fehlender Extraktion darf pro Spieler und Durchgang eine Summe manuell erfasst werden. Sie bleibt als „manuell“ markiert und ist keine Prüfzelle.
- **Gruppenfelder sind bewusst gruppenweit.** `Geprueft` und `Spieler_Name` gelten für alle zwölf Zeilen eines Spielers; `Kommentar` ist pro Zeile.
- **Externe Schema-Namen sind Verträge.** `llm/schema.py` ist der externe LLM-Vertrag. Interne Renames laufen über Aliase; `PROMPT_VERSION` steigt nur bei semantischen Prompt-/Schema-Änderungen.
- **Kosten und Secrets.** Token/Kosten pro Extraktion loggen/speichern. API-Keys nie in Logs, Datenbank oder Commits; `.env` bleibt ignoriert.

## Domänenbegriffe

`Wurf-Nr.` ist die Zeile 1–12; `Wurf` ist die Würfelkombination der Wertungstabelle. Für die Zeilen heißt das Modell `WurfZeileLLM`, das Feld `wurf_zeilen`. `BogenRef` bündelt `(bogen_id, quelle, seite)`. Ein `Durchgangsergebnis` ist die Summe eines Spielers in einem Durchgang, egal ob gescannt oder manuell.
