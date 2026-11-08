## Summary

`input/`-Scan → LLM-Transkription → Validierung → eine inkrementelle `auswertung.csv` → Excel-Pivot.

```text
input/*.jpg|*.png|*.pdf
  → LLM (DeepSeek V4.1 Flash, JSON-Schema `wurf_zeilen`)
  → Validierung (Wertung, Summenkontrolle, Normalisierung)
  → Merge in auswertung.csv
      bestehende Zeilen bleiben unverändert
      gleicher (Durchgang, Spieler) + gleiche Werte → Duplikat
      gleicher (Durchgang, Spieler) + andere Werte → Konflikt
  → Aufräumen: sauber löschen, auffällig → review/, technisch behalten
```

Die CSV ist Ausgabe **und** Zustand: `Punkte` ist die Pivot-Spalte, `Summe_Bogen` die Kontrolle, Abweichungen werden markiert statt automatisch korrigiert. Excel-Pivot: Zeilen = Spieler, Spalten = Durchgang, Werte = Summe Punkte.

## Evidence

**Before:** `60715cc` enthielt nur Beispiele und Skills, keine CLI.

**After:**

```text
$ ./scripts/check.sh
All checks passed!
33 files already formatted
0 errors, 0 warnings, 0 informations
58 passed, 1 skipped
```

Guardrails: lokal über pre-commit (Ruff, Ruff-Format, Pyright, Pytest, detect-secrets) und `scripts/check.sh`; bewusst **kein** GitHub-Actions-Workflow. Der echte Modelltest ist `--run-manual`/`scripts/smoke_test.sh` und läuft nie in `pre-commit`. `--max-cost` bricht vor dem CSV-Schreiben ab.

Echter Smoke-Test mit den drei Beispieldateien:

- `img1.jpg`: 4/4 Summen korrekt (985, 775, 470, 685), 0 offene Punkte.
- `img.jpg`: 4/4 Summen korrekt (590, 795, 760, 935); drei `8.5`-Normalisierungen markiert.
- `img2.jpg`: drei offene Punkte; zwei echte Summenabweichungen (17: 765/755, 48: 1080/1090) plus ein als 80 statt 90 gelesener Wert, alle von der Summenkontrolle markiert.
- Kombinierter Cache-Lauf: 12 Gruppen, 0 Konflikte, 6 offene Punkte, 3 Cache-Treffer, $0.

`examples/` und die Original-Scans blieben unverändert.

## Merge Danger

**Door:** Two-way für den Code (Greenfield, keine bestehenden Aufrufer). Die Entscheidung „CSV ist Ausgabe und Zustand“ ist bewusst schwerer rückgängig zu machen und in ADR-0001 dokumentiert.

**Blast Radius:** Niedrig. Neue CLI ohne bestehende Konsumenten; benötigt `OPENROUTER_API_KEY` in `.env`. Excel muss nach jedem Lauf manuell aktualisiert werden und die CSV darf währenddessen nicht geöffnet sein.
