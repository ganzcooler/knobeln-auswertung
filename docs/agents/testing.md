# Testing

Default-Suite: `uv run pytest` — schnell, ohne Netzwerk, ohne API-Key.

## Seams

- `application` — gemeinsamer Anwendungskern für Web-UI und CLI: Turnier, Durchgang, Import, Extraktion, Prüffälle, manuelle Ergebnisse, Konflikt, Rangliste, Export; temporäre SQLite-DB und Fake-LLM.
- `web` — dünne HTTP-/HTMX-Fläche: Upload, manuelle Eingabe, Prüfentscheidung, Rangliste, Offline-Banner; keine Wiederholung der Fachlogik.
- `normalize_punkte` / `normalize_summe` — reine Zell-/Summenregeln.
- `llm/client` — Request-Form, Reparatur-/Length-Retry, Cache; Fake-Client, kein Netzwerk.
- CLI — Web-Start, Import, Optionen und gemeinsame Datenbank.

## Workflow-Abdeckung

| Workflow-Schritt | Tests |
| --- | --- |
| Turnier anlegen, auswählen, umbenennen, löschen, letztes Turnier merken | `test_application_turniere.py`, `test_web_turniere.py` |
| Durchgang anlegen, auswählen, Fortschritt, Abschließen/Wiederöffnen | `test_application_workflow.py`, `test_web_workflow.py`, `test_web_ui.py` |
| Scan-Import JPG/PNG/PDF, Duplikat, Fehler, Scan-Archiv | `test_application_workflow.py`, `test_web_ui.py`, `test_web_workflow.py` |
| Extraktion, Fehler, Retry, Offline-Warten, Neustart, Kostenlimit | `test_workflow_end_to_end.py`, `test_web_ui.py`, `test_application_workflow.py` |
| Prüf-Queue, Filter, Sortierung, Bogen-Detail, Zoom, Vorschlag, zulässige Werte | `test_web_ui.py`, `test_workflow_end_to_end.py`, `test_application_workflow.py` |
| Entscheidungen: übernehmen, korrigieren, unleserlich, Undo, Kopfzeile, Bogen bestätigen, Summe akzeptieren | `test_web_ui.py`, `test_workflow_end_to_end.py`, `test_application_workflow.py` |
| Manuelle Ergebnisse: Validierung, Bearbeiten, gescannt/manuell, Offline | `test_web_ui.py`, `test_application_workflow.py`, `test_web_workflow.py` |
| Konflikte: Scan/Scan, Manuell/Scan, Auswahl, verworfen, neuer Scan öffnet wieder | `test_workflow_end_to_end.py`, `test_application_workflow.py`, `test_web_ui.py` |
| Rangliste: Durchgang, Gesamt, Gleichstand, Status, Vollbild, Leerzustand | `test_workflow_end_to_end.py`, `test_web_workflow.py`, `test_web_ui.py` |
| XLSX: Blätter, Kopfzeilen, Quelle, Status, Exportfehler | `test_workflow_end_to_end.py`, `test_application_workflow.py`, `test_web_ui.py` |
| CLI: Web-Start, Import, Pfad-Fallback, Optionen, Localhost-Bindung | `test_cli.py` |
| UI/Accessibility: Hilfe, `aria-live`, Fokus, 44-px-Ziele, Reduced Motion | `test_web_ui.py` |
| Echte Modell-Extraktion | `tests/manual/test_real_smoke.py` (manuell, kostenpflichtig) |

Die Abdeckung ist verhaltensorientiert an den bestätigten Seams; sie ist keine
zeilenweise Coverage-Garantie. Der Standardlauf ist `./scripts/check.sh`
(ohne Browser). Die echten Headless-Browser-Tests laufen separat:

```bash
uv run playwright install chromium   # einmalig
./scripts/test-browser.sh
```

Sie decken die drei Sichten im echten Chromium ab: HTMX-Statusaktualisierung,
Prüfen und Summenentscheidung, manuelle Erfassung, Rangliste/Vollbild/XLSX-
Download, Hilfe-Dialog inklusive `?`/`Esc`, Konfliktauswahl, Löschbestätigung
und Tablet-Viewport/44-px-Ziele. Auf Systemen ohne passende Systembibliotheken
hilft `uv run playwright install-deps chromium` (sudo).

## Echter Modelltest

Nur manuell und kostenpflichtig:

```bash
uv run pytest --run-manual
```

Der echte Test importiert ein Beispiel über den neuen Anwendungskern und prüft, dass die Extraktion vier Spielergruppen liefert. Er läuft nie in den lokalen Standard-Checks oder in `pre-commit`.
