# Testing

Default-Suite: `uv run pytest` — schnell, ohne Netzwerk, ohne API-Key.

## Seams

- `application` — gemeinsamer Anwendungskern für Web-UI und CLI: Turnier, Durchgang, Import, Extraktion, Prüffälle, manuelle Ergebnisse, Konflikt, Rangliste, Export; temporäre SQLite-DB und Fake-LLM.
- `web` — dünne HTTP-/HTMX-Fläche: Upload, manuelle Eingabe, Prüfentscheidung, Rangliste, Offline-Banner; keine Wiederholung der Fachlogik.
- `normalize_punkte` / `normalize_summe` — reine Zell-/Summenregeln.
- `llm/client` — Request-Form, Reparatur-/Length-Retry, Cache; Fake-Client, kein Netzwerk.
- CLI — Web-Start, Import, Optionen und gemeinsame Datenbank.

## Echter Modelltest

Nur manuell und kostenpflichtig:

```bash
uv run pytest --run-manual
```

Der echte Test importiert ein Beispiel über den neuen Anwendungskern und prüft, dass die Extraktion vier Spielergruppen liefert. Er läuft nie in den lokalen Standard-Checks oder in `pre-commit`.
