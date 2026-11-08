# Knobeln-Auswertung — Spec

Status: ready-for-agent
Feature: `knobeln-auswertung`

## 1. Ziel

Eine CLI ohne UI wertet gescannte Knobeln-Protokollbögen aus. Ein Vision-LLM liest die handgeschriebenen Punkte, die App validiert sie gegen die gedruckte Wertung und pflegt daraus **eine** Excel-pivotfähige CSV. Die von den Spielern selbst gerechnete Summenzeile ist eine Kontrolle: Weicht sie von der berechneten Summe ab, wird der Bogen in der CSV markiert und menschlich geprüft. Die App korrigiert die Summe nie automatisch.

## 2. Nicht-Ziele

- Keine GUI, kein Webserver.
- Kein automatisches Korrigieren der Summenzeile.
- Keine Pivot-Erzeugung in der App; die Pivot baut der Mensch in Excel.
- Kein Datenbank-Backend; die CSV ist Ausgabe und Zustand.
- Keine Unterstützung anderer Bogen-Layouts, Vereine oder Punktesysteme in v1.
- Kein Tesseract-/OCR-Fallback; die Handschrift wird ausschließlich per LLM gelesen.
- Keine automatische Löschung eines Scans vor einem erfolgreichen CSV-Schreiben.

## 3. Begriffe und Regeln

Die kanonischen Begriffe stehen in [`GLOSSARY.md`](../../GLOSSARY.md). Kurzfassung:

- **Bogen**: eine Seite mit vier Spielerspalten, zwölf Wurf-Zeilen und einer Summenzeile.
- **Durchgang**: handgeschriebene Runde, gültig 1–5. Ein Durchgang kann mehrere Bögen mit je vier Spielern enthalten.
- **Spieler**: identifiziert durch `Spieler_Nr`; der Name ist optional.
- **Wurf-Nr.**: Zeile 1–12. Nicht zu verwechseln mit dem „Wurf“ der Wertungstabelle.
- **Punkte**: 0 (Schrägstrich oder geschriebene 0) oder ein Wert aus der Wertungstabelle.
- **Summenzeile**: die selbst gerechnete Summe pro Spieler. Kontrolle, keine Korrekturquelle.
- **Duplikat**: gleicher `(Durchgang_Nr, Spieler_Nr)` mit identischen Werten. Wird übersprungen.
- **Konflikt**: gleicher `(Durchgang_Nr, Spieler_Nr)` mit abweichenden Werten. Wird gemeldet, nicht überschrieben.
- **Eingang**: der Ordner `input/` mit noch nicht verarbeiteten Scans.
- **Stern-Regel**: existiert für diese App nicht. Die `*`-Markierung der Wertung wird ignoriert.

### 3.1 Gültige Punktwerte

Die gedruckte Wertung ist für das gesamte Spiel konstant und auf jedem Bogen gleich. Gültig sind:

```text
0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75,
80, 85, 90, 95, 100, 105, 110, 120, 130, 140, 150, 160, 170, 200
```

Die Wertung im Überblick (die App liest die Würfelkombination nicht, sie braucht nur die Punktwerte):

| Wurf | Punkte | Wurf | Punkte |
| --- | ---: | --- | ---: |
| 104 | 5 | 202 | 80 |
| 105 | 10 | 203 | 85 |
| 106 | 15 | 204 | 90 |
| 107 | 20 | 205 | 95 |
| 108 | 25 | 220 | 100 |
| 109 | 30 | 260 | 105 |
| 110 | 35 | 300 | 110 |
| 122 | 40 | 222* | 120 |
| 123 | 45 | 333* | 130 |
| 124 | 50 | 444* | 140 |
| 125 | 55 | 555* | 150 |
| 162 | 60 | 666* | 160 |
| 163 | 65 | 111* | 170 |
| 164 | 70 | 123* | 200 |
| 165 | 75 | | |

Werte, die nicht in dieser Liste stehen (z. B. 115, 125, 135, 145, 155, 165, 175, 180, 185, 190, 195), sind ungültig.

### 3.2 Zellwerte und Korrektur

- `/` oder `\` bedeutet **0**.
- Eine geschriebene `0` bedeutet **0**.
- Eine leere Zelle bedeutet **fehlend**, nicht 0.
- Domänenkonstante Korrektur nur bei Trennzeichen-Artefakten: Wenn das Entfernen von `.`, `,`, `'` oder Leerzeichen einen Wert aus der Wertung ergibt, wird dieser Wert übernommen. Beispiele: `8.5` → 85, `10.5` → 105, `1.5` → 15, `8.0` → 80. Jede solche Korrektur erzeugt einen Eintrag in `Korrektur` und eine Warnung.
- Kein Runden auf den nächsten 5er, kein Klemmen auf 0/200. Ist der bereinigte Wert nicht in der Wertung, bleibt `Punkte` leer und es gibt `wert_ungueltig`.
- Die Summenzeile wird nie benutzt, um Zellwerte zu erraten oder zu korrigieren.

## 4. Eingang und Verarbeitung

- Standard-Eingang: `input/` (per `--input` änderbar). Der Ordner wird bei Bedarf angelegt.
- Unterstützte Dateien: `.jpg`, `.jpeg`, `.png`, `.pdf`, rekursiv.
- Versteckte Dateien (z. B. `.DS_Store`, `._*`) werden ignoriert. Nicht unterstützte Dateien bleiben liegen und erzeugen eine Warnung; sie werden nicht gelöscht.
- Bei jedem Aufruf wird **alles** im Eingang verarbeitet, in sortierter Reihenfolge. Es wird angenommen, dass dort nur neue Scans liegen.
- Eine PDF-Seite ist ein Bogen. `Bogen_ID` = Kurz-Hash des Dateiinhalts + Seitennummer (z. B. `a1b2c3d4e5f6-p1`).
- Ist eine `Bogen_ID` bereits in der CSV und wurde `--reprocess` nicht gesetzt, wird der LLM-Aufruf übersprungen. Das dient der Crash-Wiederaufnahme; die Datei kann danach aufgeräumt werden.
- Die CSV wird erst geschrieben, wenn alle verarbeiteten Ergebnisse gemerged sind.
- **Erst nach erfolgreichem CSV-Schreiben** wird der Eingang aufgeräumt:
  - Sauber verarbeitete Dateien werden gelöscht.
  - Auffällige Dateien (`Status != ok`, `Konflikt=ja` oder `bogen_unklar`) werden nach `review/` verschoben.
  - Technische Fehler (API-Fehler, ungültiges JSON nach Retries, PDF-Seite nicht lesbar, CSV gesperrt) lassen die Datei in `input/` für den nächsten Versuch.
- Bei mehrseitigen PDFs wird die Datei erst entfernt, wenn alle Seiten verarbeitet sind. Scheitert eine Seite technisch, bleibt das PDF in `input/`; die erfolgreichen Seiten werden beim nächsten Lauf über ihre `Bogen_ID` übersprungen. Ist eine Seite inhaltlich unleserlich, wird das PDF nach `review/` verschoben; die erfolgreichen Seiten stehen bereits in der CSV.
- `review/` behält den relativen Pfad bei. Bei Namenskollisionen wird ein Hash-Suffix angehängt.
- Ist `input/` leer, wird die bestehende CSV revalidiert (Summen, Delta, Status, Warnungen neu berechnen) und mit Exit 0 beendet, sofern keine offenen Prüfpunkte bestehen.
- `--keep-input` deaktiviert das Löschen/Verschieben (Debugging).
- `--reprocess` ignoriert die `Bogen_ID`-Sperre und liest die Datei erneut (umgeht auch den LLM-Cache); bestehende CSV-Zeilen werden trotzdem nicht überschrieben, sondern nur auf Konflikte geprüft.
- `--dry-run` verarbeitet und validiert, schreibt aber keine CSV und räumt den Eingang nicht auf.

## 5. CLI

Konsolenkommando: `knobeln`.

```text
knobeln [OPTIONS]

  --input PATH        Eingangsordner (Default: input)
  --output PATH       CSV-Datei (Default: auswertung.csv)
  --review PATH       Review-Ordner (Default: review)
  --model MODEL       OpenRouter-Modell (Default: deepseek/deepseek-v4.1-flash)
  --reasoning EFFORT  Reasoning-Effort (Default: max)
  --reset             Neue Veranstaltung: bestehende CSV nach Rückfrage archivieren
  --yes               Rückfragen automatisch bestätigen
  --reprocess         Bekannte Bogen_IDs erneut lesen (umgeht auch den Cache)
  --no-cache          LLM-Cache umgehen
  --keep-input        Eingang nach dem Lauf nicht aufräumen (Debugging)
  --dry-run           Nicht schreiben und nicht aufräumen
  --backup            Vor dem Schreiben auswertung.csv.bak anlegen
  --verbose           Ausführliche Ausgabe
  --version           Version anzeigen
```

- Konfiguration aus `.env` im Arbeitsverzeichnis: `OPENROUTER_API_KEY` (Pflicht), optional `KNOBELN_MODEL`, `KNOBELN_INPUT`, `KNOBELN_OUTPUT`, `KNOBELN_REASONING`.
- CLI-Flags überschreiben Env-Werte.
- Fehlt der API-Key, bricht die App vor dem ersten Scan mit einer klaren Meldung ab (Exit 1).
- Zusammenfassung am Ende: Dateien gelesen, neue Spieler, Duplikate, Konflikte, Warnungen, unleserliche Bögen, gelöscht/verschoben/behalten, Token, Cache-Treffer und geschätzte Kosten.
- Exit-Codes:
  - `0`: alles sauber oder alle Warnungen bereits mit `Geprueft=ja` bestätigt.
  - `2`: CSV geschrieben, aber offene Prüfpunkte (`Geprueft=nein` mit Warnung/Konflikt) oder Dateien im Eingang behalten. `--keep-input` ist Debugging und zählt nicht als Prüfpunkt.
  - `1`: fataler Fehler, keine CSV-Änderung und kein Aufräumen (API-Key fehlt, CSV gesperrt, Konfiguration unlesbar).

## 6. LLM-Pipeline

- Provider: OpenRouter über die OpenAI-kompatible Chat-Completions-API.
- Modell: `deepseek/deepseek-v4.1-flash`.
- Parameter: `temperature=0`, `reasoning={"effort": "max", "exclude": true}`, hohes `max_tokens` (262144, damit trotz maximalem Reasoning genug Platz für das JSON bleibt), `response_format` mit JSON-Schema.
- Ein Aufruf pro Bogen-Seite. Bei 429/5xx/Timeout: zwei Retries mit Backoff. Bei `finish_reason=length` (Reasoning hat das Budget aufgebraucht): `max_tokens` verdoppeln (bis 524288) und erneut versuchen. Bei ungültigem JSON oder einem Schema-Verstoß (z. B. nicht genau vier Spieler bzw. zwölf Wurf-Zeilen): ein Reparatur-Retry mit derselben Antwort und klarer Fehlermeldung; danach technischer Fehler, Datei bleibt im Eingang.
- Der Prompt ist deutsch und enthält:
  - Layout: 4 Spielerspalten, 12 Wurf-Zeilen, Summenzeile.
  - Die vollständige Liste der gültigen Punktwerte.
  - Regeln: `/` = 0, leere Zelle = `null`, Trennzeichen-Artefakte normalisieren, nicht raten, Summenzeile nicht als Korrekturquelle benutzen.
  - Aufgabe: `Durchgang_Nr` (1–5), pro Spieler `Spieler_Nr`, `Spieler_Name`, 12 Zellen mit `roh` und `punkte`, sowie die gelesene Summenzeile.
  - Bei nicht erkennbarem Layout: `bogen_unklar=true` und `hinweis`.
  - Ausgabe ausschließlich JSON.
- JSON-Schema (vereinfacht):

```json
{
  "bogen_unklar": false,
  "hinweis": null,
  "durchgang_nr": 1,
  "spieler": [
    {
      "position": 1,
      "spieler_nr": "41",
      "spieler_name": "V. Spelow",
      "wurf_zeilen": [
        {"wurf_nr": 1, "roh": "110", "punkte": 110, "hinweis": null}
      ],
      "summe_bogen": {"roh": "590", "punkte": 590, "hinweis": null}
    }
  ]
}
```

- Cache: Schlüssel = `Bogen_ID` + Modell + Prompt-Version + Reasoning-Effort. Ablage unter `.cache/knobeln/`. `--no-cache` umgeht ihn.
- Tokenverbrauch und geschätzte Kosten werden pro Datei und gesamt geloggt. Der API-Key wird nie geloggt oder in die CSV geschrieben.

## 7. Validierung

### 7.1 Bogen

- Vier Spielerpositionen und zwölf Wurf-Zeilen pro Spieler werden erwartet. Fehlende Positionen/Zellen werden als leere Werte geführt und markiert, nicht stillschweigend weggelassen.
- `Durchgang_Nr` muss 1–5 sein. Fehlt sie oder liegt sie außerhalb: `Durchgang_Nr` leer, `durchgang_unklar`.
- `Spieler_Nr` muss vorhanden sein. Fehlt sie: `spieler_unklar`; die Gruppe wird trotzdem mit zwölf Zeilen geführt.
- Ist der Bogen insgesamt nicht lesbar: eine Platzhalterzeile mit `Status=bogen_unklar`.
- Teilweise unleserliche Spieler: zwölf Zeilen mit leeren `Punkte`, `spieler_unklar`.

### 7.2 Zellen

- `Punkte` muss in der Wertungsliste (inkl. 0) stehen.
- Leere Zelle: `Punkte` leer, `wert_fehlt`.
- Nicht normalisierbarer Wert: `Punkte` leer, `wert_ungueltig`.
- Normalisierter Wert: `Punkte` gesetzt, `Korrektur`-Notiz, `wert_korrigiert`.

### 7.3 Summen

- `Summe_Bogen_Roh` ist die rohe LLM-Lesung der Summenzeile; `Summe_Bogen` ist der finale Wert. `/` = 0, leer = fehlend.
- Wurde `Summe_Bogen` aus dem Rohwert normalisiert, gibt es `summe_korrigiert` und einen Hinweis.
- `Summe_Berechnet` = Summe der zwölf `Punkte`, aber nur wenn alle zwölf Werte vorhanden sind; sonst leer und `summe_unvollstaendig`.
- `Delta = Summe_Bogen - Summe_Berechnet`, wenn beide vorhanden.
- `Delta != 0` → `summe_abweichung`.
- `Summe_Bogen` fehlt → `summe_fehlt`.
- `Summe_Bogen` ist keine 5er-Zahl oder liegt außerhalb 0–2400 → `summe_ungueltig`.
- Die App korrigiert `Punkte` nie anhand der Summenzeile.

### 7.4 Identität, Duplikate, Konflikte

- Fachlicher Schlüssel: `(Durchgang_Nr, Spieler_Nr)`.
- Gleicher Schlüssel, identische zwölf `Punkte` und identische `Summe_Bogen`: Duplikat, wird übersprungen.
- Gleicher Schlüssel, abweichende Werte: Konflikt. Bestehende Zeilen bleiben unverändert; `Konflikt=ja`, `Status=konflikt`, `Warnung` mit den Unterschieden (z. B. `W03: bestehend 95, neu 85`). Der neue Scan wird nicht angehängt.
- Neuer Schlüssel: zwölf Zeilen werden angehängt.
- Gleicher Schlüssel, nur anderer Name: `name_konflikt`; bei identischen Punkten wird der neue Scan als Duplikat übersprungen.
- Gleiche `Spieler_Nr` zweimal auf demselben Bogen: beide Gruppen werden geführt, `spieler_doppelt` markiert; der Mensch korrigiert eine der Nummern.
- Beim `--reprocess` wird eine bestehende Gruppe zuerst über `Bogen_ID + Spieler_Position` erkannt. Weicht die neu gelesene Identität von der bestehenden ab, wird `identitaet_konflikt` gemeldet und die bestehende Identität nicht überschrieben.
- Namens-Kanonisierung: Fehlende Namen werden pro `Spieler_Nr` aus einem eindeutigen nicht-leeren Namen ergänzt. Gibt es mehrere verschiedene Namen, bleiben die gelesenen/korrigierten Namen stehen und es gibt `name_konflikt`.
- Menschliche Korrekturen werden nie überschrieben; sie bleiben maßgeblich. Ein abweichender neuer Scan wird trotzdem als Konflikt gemeldet, bis der Mensch ihn mit `Geprueft=ja` bestätigt oder die Werte erneut korrigiert.

### 7.5 `Geprueft`

- `Geprueft=ja` bedeutet: Der Mensch hat den Prüfpunkt angesehen. Die App öffnet denselben Konflikt nicht erneut.
- Der Status kann trotzdem den sachlichen Befund nennen (`summe_abweichung|geprueft`); für den Exit-Code zählt `Geprueft=ja` als erledigt.
- Kommt später ein neuer, abweichender Scan für denselben Schlüssel, wird `Geprueft` wieder auf `nein` gesetzt und der Konflikt erneut geöffnet.

### 7.6 Status-Codes

Mehrere Codes werden mit `|` verbunden; `ok` steht nur allein. Die Warnungsspalte enthält den deutschen Klartext.

```text
ok
bogen_unklar
durchgang_unklar
spieler_unklar
spieler_doppelt
wert_fehlt
wert_ungueltig
wert_korrigiert
summe_fehlt
summe_ungueltig
summe_unvollstaendig
summe_abweichung
summe_korrigiert
name_konflikt
konflikt
identitaet_konflikt
geprueft
```

## 8. CSV

### 8.1 Format

- Datei: `auswertung.csv` (per `--output` änderbar), fester Pfad.
- UTF-8 mit BOM, Trennzeichen `;`, eine Kopfzeile, keine Leerzeilen, keine Zwischensummen-Zeilen. Geschrieben wird immer `;`; beim Lesen wird auch ein komma-getrennter Excel-Zwischenstand erkannt.
- Standard-CSV-Quoting.
- Eine Zeile pro Wurf. Pro Spieler zwölf Zeilen. Für einen unleserlichen Bogen eine Platzhalterzeile mit leerem `Wurf_Nr`.
- Wiederholte Spieler-Metadaten auf allen zwölf Zeilen sind beabsichtigt, damit die Pivot sauber bleibt.

### 8.2 Spalten

| Spalte | Typ | Bedeutung | Hoheit |
| --- | --- | --- | --- |
| `Bogen_ID` | Text | Hash der Quelle + Seite | App |
| `Quelle` | Text | ursprünglicher Pfad im Eingang | App |
| `Seite` | Ganzzahl | Seite der Quelle, 1-basiert | App |
| `Spieler_Position` | Ganzzahl 1–4 | Spalte auf dem Bogen | App |
| `Durchgang_Nr` | Ganzzahl/leer | 1–5 | App, Mensch darf korrigieren |
| `Spieler_Nr` | Text | Spieler-Nummer | App, Mensch darf korrigieren |
| `Spieler_Name` | Text | optionaler Name | App, Mensch darf korrigieren |
| `Wurf_Nr` | Ganzzahl 1–12 | Zeile auf dem Bogen | App |
| `Punkte` | Ganzzahl/leer | finale Punkte, Pivot-Wert | App initial, Mensch korrigiert |
| `Punkte_Roh` | Text | rohe LLM-Lesung | App, nicht bearbeiten |
| `Korrektur` | Text | App-Notiz zur Normalisierung | App |
| `Summe_Bogen_Roh` | Text | rohe LLM-Lesung der Summenzeile | App, nicht bearbeiten |
| `Summe_Bogen` | Ganzzahl/leer | gelesene Summenzeile | App, Mensch darf korrigieren |
| `Summe_Berechnet` | Ganzzahl/leer | Summe der zwölf `Punkte` | App |
| `Delta` | Ganzzahl/leer | `Summe_Bogen - Summe_Berechnet` | App |
| `Status` | Text | Status-Codes | App |
| `Warnung` | Text | Klartext-Warnung | App |
| `Konflikt` | `ja`/`nein` | offener Datenkonflikt | App |
| `Konflikt_Detail` | Text | Unterschiede des Konflikts (z. B. `W03: bestehend 95, neu 85`) | App |
| `Namenskonflikt` | Text | konkurrierende Namen, mit `\|` getrennt | App |
| `Geprueft` | `ja`/`nein` | menschlich bestätigt | Mensch |
| `Kommentar` | Text | freie Notiz pro Zeile | Mensch |

- Bestehende Zeilen werden in den Inhaltsspalten nie überschrieben. Die App aktualisiert nur die abgeleiteten Spalten (`Summe_Berechnet`, `Delta`, `Status`, `Warnung`, `Konflikt`) und ergänzt fehlende Namen. `Kommentar` bleibt pro Zeile erhalten; `Namenskonflikt` wird von der App gepflegt. Ausnahme: Ein `bogen_unklar`-Platzhalter wird durch lesbare Daten ersetzt, wenn derselbe Scan erneut gelesen wird.
- Unbekannte Spalten werden beim Merge beibehalten, damit eigene Notizen nicht verloren gehen. Bekannte Spalten dürfen nicht umbenannt werden.
- Die CSV wird atomar geschrieben (temporäre Datei + Replace). Bei einem Schreibfehler bleibt die alte Datei unverändert. `--backup` kann vorher eine Kopie `auswertung.csv.bak` anlegen.

### 8.3 Pivot in Excel

1. CSV einmal als Datenquelle verbinden (Daten → Aus Text/CSV, Trennzeichen `;`, UTF-8).
2. Pivot: Zeilen = `Spieler_Nr` (optional `Spieler_Name`), Spalten = `Durchgang_Nr`, Werte = Summe von `Punkte`.
3. Für Prüfungen nach `Status`, `Konflikt` oder `Geprueft` filtern.
4. Nach jedem App-Lauf „Alle aktualisieren“. Excel beobachtet die Datei nicht von selbst; optional ein Refresh-Intervall setzen.
5. Die CSV vor dem App-Lauf in Excel schließen, sonst kann Windows die Datei sperren.

## 9. Merge-Algorithmus

1. Bestehende CSV lesen; fehlt sie, mit Kopfzeile beginnen. Schema prüfen, fehlende bekannte Spalten leer ergänzen, unbekannte Spalten beibehalten.
2. Bestehende Zeilen indexieren:
   - `(Bogen_ID, Spieler_Position, Wurf_Nr)` für dieselbe Quelle/Seite.
   - `(Durchgang_Nr, Spieler_Nr)` für den fachlichen Duplikat-/Konfliktvergleich.
3. Eingangsdateien sortiert verarbeiten. Pro Datei/Seite `Bogen_ID` berechnen; bekannte IDs ohne `--reprocess` überspringen.
4. LLM-Antwort validieren und in eine Bogen-Struktur überführen (4 Spieler × 12 Wurf-Zeilen, auch bei fehlenden Werten).
5. Pro Spielergruppe:
   - Existiert `(Bogen_ID, Spieler_Position)` (Reprocess): Identität und Werte vergleichen; bei Abweichung `identitaet_konflikt` bzw. `konflikt`, bestehende Werte nicht überschreiben.
   - Sonst existiert `(Durchgang_Nr, Spieler_Nr)`: gleiche Werte → Duplikat überspringen; abweichende Werte → Konflikt auf der bestehenden Gruppe markieren; nicht anhängen.
   - Sonst: zwölf Zeilen anhängen.
6. Abgeleitete Spalten für alle Gruppen neu berechnen: `Summe_Berechnet`, `Delta`, `Status`, `Warnung`, `Konflikt`; `Geprueft` und `Kommentar` bleiben unangetastet, außer ein neuer abweichender Scan öffnet `Geprueft` wieder. Namens-Kanonisierung anwenden.
7. CSV atomar schreiben.
8. Eingang aufräumen (sauber löschen, auffällig nach `review/`, technisch behalten).
9. Zusammenfassung ausgeben und Exit-Code setzen.

## 10. Aufräumen

- **Sauber**: alle Gruppen der Datei haben `Status=ok` oder sind vollständig mit `Geprueft=ja` bestätigt. Datei löschen.
- **Auffällig**: mindestens eine Gruppe hat einen Warn-/Konfliktstatus oder `bogen_unklar`. Datei nach `review/` verschieben.
- **Technisch**: API-/JSON-/PDF-Fehler. Datei bleibt in `input/`.
- **Duplikat**: Wenn die bestehende Gruppe sauber ist, Datei löschen; ist sie auffällig, nach `review/` verschieben.
- Nicht unterstützte Dateien bleiben liegen und werden gemeldet.
- Aufräumen erst nach erfolgreichem CSV-Schreiben. Bei einem Fehler wird nichts gelöscht/verschoben.

## 11. Fehlerbehandlung

- API-Key fehlt: Exit 1, klare Meldung, keine Verarbeitung.
- API nicht erreichbar / Rate Limit / Timeout: Retries, dann Datei in `input/` behalten, Exit 2.
- Ungültiges JSON: Reparatur-Retry, dann Datei behalten, Exit 2.
- CSV gesperrt oder Schreibfehler: keine Datei anfassen, Exit 1.
- Unbekanntes Modell / API-Fehler: nach Retries Datei behalten, Exit 2.
- Unsupported file: Warnung, Datei bleibt, Exit 2.
- Keine Secrets in Logs oder CSV.
- `--reset`: bestehende CSV nach Rückfrage nach `auswertung.<timestamp>.bak.csv` verschieben und neu beginnen; ohne `--yes` nicht löschen.

## 12. Projektstruktur

```text
pyproject.toml
src/knobeln/
  __init__.py
  cli.py
  config.py
  pipeline.py
  domain/
    models.py
    wertung.py
    normalize.py
    validation.py
    merge.py
  llm/
    client.py
    models.py
    mapping.py
    prompt.py
    schema.py
    cache.py
  io/
    input_scanner.py
    pdf.py
    csv_store.py
    csv_mapping.py
    cleanup.py
tests/
  fixtures/
  test_*.py
```

- Python 3.13, `uv`, `pyproject.toml`.
- Abhängigkeiten: `openai` (OpenAI-kompatibler Client), `pydantic`, `python-dotenv`, `pypdfium2`, `Pillow`, `typer`, `rich`; Tests mit `pytest`.
- `.env.example` mit `OPENROUTER_API_KEY=`.
- `.gitignore`: `.env`, `input/*`, `review/*`, `auswertung.csv`, `*.bak`, `*.bak.csv`, `.cache/`, `.venv/`, `__pycache__/`.
- `input/` und `review/` werden bei Bedarf angelegt.

## 13. Tests und Abnahme

### 13.1 Unit-Tests

- Normalisierung: `/`→0, `0`→0, `8.5`→85, `10.5`→105, `1.5`→15, `8.0`→80, `115`→ungültig, `87`→ungültig, `205`→ungültig, leer→fehlend.
- Summen: vollständig, unvollständig, fehlend, Delta, 5er-Regel.
- Status-Kombinationen und `Geprueft`.
- CSV: Semikolon, BOM, Kopfzeile, Quoting, leere Werte.
- Merge: neu anhängen, Duplikat überspringen, Konflikt nicht überschreiben, menschliche Korrektur erhalten, `Geprueft`, Namenskonflikt, unleserlicher Bogen.
- Aufräumen: sauber löschen, auffällig nach `review/`, technisch behalten, PDF-Mehrseiter.
- `--reset`, `--keep-input`, `--dry-run`.

### 13.2 Integration mit Fake-LLM

- Drei Fixtures aus `examples/` mit handgeschriebenen Fake-LLM-Antworten.
- Pipeline in einem temporären Verzeichnis ausführen; CSV und Aufräumverhalten prüfen.
- Erwartete Summen (von den Bögen):
  - `img.jpg`: 590, 795, 760, 935. `8.5`/`9.5` werden zu 85/95 normalisiert.
  - `img1.jpg`: 985, 775, 470, 685.
  - `img2.jpg`: 765, 1080, 735, 645. Die Fake-Fixture bildet die Abweichung von Spieler 17 nach (Bogen 765, berechnet 755).
- Die Fixtures sind Golden-Daten für die Merge-/Validierungslogik, nicht für die echte Modellgenauigkeit. Die echten Smoke-Test-Ergebnisse (inkl. Spieler 48: Bogen 1080, berechnet 1090) stehen in Issue 09.

### 13.3 Echter Modell-Smoke-Test

- Ausgeführt am 2026-11-08; Ergebnisse in `.scratch/knobeln-auswertung/issues/09-real-model-smoke-test.md`.
- Nur `deepseek/deepseek-v4.1-flash` mit `reasoning.effort="max"`.
- Bei künftigen Änderungen erneut Zelltreffer, Summenkontrolle, Laufzeit und Kosten dokumentieren. Kein Wechsel auf ein teureres Modell ohne Rückfrage.

## 14. Später

- Andere Bogen-Layouts, Vereine oder Punktesysteme.
- Automatischer Excel-Refresh / Power-Query-Vorlage.
- Parallele Verarbeitung mehrerer Scans.
- GUI oder Review-Ansicht.
- Zusätzliche Modelle/Provider.
