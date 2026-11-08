# 08 — Tests, Fixtures und Fake-LLM

Status: resolved
Blocked by: 02, 03, 04, 05, 06

## Ziel

Die gesamte Logik ohne Netzwerk und ohne API-Key testen. Die drei Beispielbögen dienen als Fixtures; die echte Modellgenauigkeit wird separat geprüft.

## Aufgaben

- Unit-Tests für Domäne, CSV-Format, Merge, Konflikte, Aufräumen und CLI-Config.
- Fixtures aus `examples/img.jpg`, `examples/img1.jpg`, `examples/img2.jpg`; handgeschriebene Fake-LLM-Antworten als Golden-Daten.
- Integrationstest: temporäres `input/`, Fake-Client, Pipeline, CSV prüfen, Aufräumverhalten prüfen.
- PDF-Test mit einem kleinen erzeugten mehrseitigen PDF.
- Test für gesperrte CSV (Mock/PermissionError) und `--dry-run`, `--keep-input`, `--reset`.
- Test für menschliche Korrektur + `Geprueft` + erneuten Lauf.
- Keine Netzwerkaufrufe in der Testsuite.

## Abnahmekriterien

- `uv run pytest` läuft grün und benötigt keinen API-Key.
- Die Golden-Daten markieren die Abweichung in `img2` (Spieler 172: Bogen 765, berechnet 755).
- `8.5`/`9.5` in `img.jpg` werden als 85/95 geführt, ohne Summenwarnung.
- Merge-, Konflikt- und Aufräumfälle sind abgedeckt.
- Ein fehlender Key führt im Test zu Exit 1, nicht zu einem Netzwerkaufruf.

## Referenzen

- `../spec.md` §13.1, §13.2
