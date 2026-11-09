# Testing

Default-Suite: `uv run pytest` — schnell, ohne Netzwerk, ohne API-Key.

## Seams

- `application` — gemeinsamer Anwendungskern für Web-UI und CLI: Turnier, Durchgang, Import, Extraktion, Prüffälle, manuelle Ergebnisse, Konflikt, Rangliste; temporäre SQLite-DB und Fake-LLM.
- `web` — dünne HTTP-/HTMX-Fläche: Upload, manuelle Eingabe, Prüfentscheidung, Rangliste, Offline-Banner; keine Wiederholung der Fachlogik.
- `normalize_punkte` / `normalize_summe` — reine Zell-/Summenregeln.
- `merge_gruppen` — Duplikat-, Konflikt- und `Geprueft`-Verhalten.
- `csv_store` / `csv_mapping` — Roundtrip, unbekannte Spalten, `Kommentar` pro Zeile (Altpfad, wird mit Ticket 14 entfernt).
- `llm/client` — Request-Form, Reparatur-/Length-Retry, Cache; Fake-Client, kein Netzwerk.
- `pipeline` — Eingang, Aufräumen, Kostenlimit, Exit-Codes; Fake-LLM (Altpfad, wird mit Ticket 14 entfernt).
- CLI — Optionen, Konfiguration, fehlender Key, Web-Start und Import.

## Echter Modelltest

Nur manuell und kostenpflichtig:

```bash
./scripts/smoke_test.sh          # drei Beispiele, Golden-Vergleich
uv run pytest --run-manual       # derselbe Smoke-Test als pytest
```

Golden-Daten liegen unter `tests/manual/golden/`. Der echte Test läuft nie in den lokalen Standard-Checks oder in `pre-commit`.
