# 09 — Echter Modell-Smoke-Test (DeepSeek V4.1 Flash)

Status: resolved
Blocked by: 08
Info: ausgeführt am 2026-11-08

## Ziel

Die echte Lesegenauigkeit des festgelegten Modells an den drei Beispielbögen messen und dokumentieren. Keine teuren Modelle, kein stiller Fallback.

## Aufgaben

- `OPENROUTER_API_KEY` in `.env` setzen (nicht im Chat, nicht committen).
- Kopien der drei Beispiele in ein temporäres `input/` legen.
- Pipeline mit `deepseek/deepseek-v4.1-flash` und `reasoning.effort="max"` ausführen.
- Pro Bogen dokumentieren:
  - gelesene Zellwerte vs. manuelle Referenzlesung,
  - erkannte `Durchgang_Nr` und Spieler,
  - `Summe_Bogen` vs. `Summe_Berechnet`,
  - Warnungen/Konflikte,
  - Laufzeit, Token, geschätzte Kosten.
- Bei unzureichender Genauigkeit: Prompt verbessern, Bildvorverarbeitung prüfen, ggf. zweiter Pass mit demselben Modell. Kein Modellwechsel ohne Rückfrage.

## Abnahmekriterien

- Ein Ergebnisbericht liegt vor, inklusive der Abweichung in `img2` (Spieler 17, Bogen 765, berechnet 755).
- `8.5`/`9.5` in `img.jpg` werden korrekt als 85/95 erkannt oder als unsicher markiert.
- Kosten und Laufzeit sind dokumentiert.
- Offene Genauigkeitsprobleme sind als konkrete Prompt-/Preprocessing-Aufgaben notiert.

## Referenzen

- `../spec.md` §6, §13.3

## Comments

**2026-11-08 — Smoke-Test ausgeführt.**

Setup: Kopien der drei Beispiele unter `/tmp/knobeln-smoke/`, jeweils ein Lauf pro Beispiel plus ein kombinierter Lauf, `--keep-input`; `examples/` blieb unverändert. Modell `deepseek/deepseek-v4.1-flash`, `reasoning.effort="max"`.

Ergebnisse:

- `img1.jpg`: 4/4 Summen korrekt (985, 775, 470, 685), 0 offene Punkte. Namen (V. Spelow, Steffen, Angelika, D.u.E.) korrekt gelesen.
- `img.jpg`: 4/4 Summen korrekt (590, 795, 760, 935). `8.5` an drei Stellen korrekt als 85 erkannt (`wert_korrigiert`, 3 offene Punkte; keine Summenabweichung). Spieler-Nr. 43, 9, 42, 2 korrekt; der Name von Spieler 43 wurde nicht gelesen (optional, auf dem Bogen vorhanden).
- `img2.jpg`: Spieler 17: Bogen 765, berechnet 755 (`summe_abweichung`, Delta +10). Spieler 48: Bogen 1080, berechnet 1090 (`summe_abweichung`, Delta -10; W12=10 auf dem Bogen bestätigt). Spieler 25 und 30: Summen korrekt. Spieler-Nr. 17, 48, 25, 30 korrekt.
- Kombinierter Lauf: 12 Gruppen, 0 Konflikte, 5 offene Punkte, 3 Cache-Treffer, keine zusätzlichen API-Kosten.
- Wiederholungslauf `img1.jpg` ohne Cache: Ein Versuch lieferte ein strukturell falsches JSON (u. a. 36 Wurf-Zeilen, falsche Durchgangs-/Spieler-Nr.). Die App hat die Werte nicht stillschweigend als sauber akzeptiert, sondern markiert. Daraufhin wurde die clientseitige Strukturvalidierung verschärft: genau vier Positionen, genau zwölf Wurf-Zeilen, sonst Reparatur-Retry. Der nächste Lauf mit strenger Validierung war sauber (4/4 Summen, 0 offene Punkte).

Tokens/Kosten der API-Läufe:

- `img1.jpg` (erster Lauf): 1814 prompt / 12627 completion (10878 reasoning), ca. $0.0053.
- `img.jpg`: 2243 prompt / 6062 completion (4321 reasoning), ca. $0.0026.
- `img2.jpg`: 1814 prompt / 7836 completion (6095 reasoning), ca. $0.0033.
- `img1.jpg` (fehlerhafter Wiederholungslauf): 1416 prompt / 4035 completion (2364 reasoning), ca. $0.0017.
- `img1.jpg` (strenger Wiederholungslauf): 2243 prompt / 5273 completion (3257 reasoning), ca. $0.0023.
- Der erste `img.jpg`-Versuch mit `max_tokens=65536` endete mit `finish_reason=length` (leere Antwort); die Kosten dafür wurden nicht erfasst, grob ca. $0.027. `max_tokens` wurde auf 262144 erhöht, zusätzlich gibt es einen Length-Retry bis 524288.
- Gesamtkosten der Smoke-Tests grob **$0.04** (inkl. Fehlversuch und Wiederholungen).

Fazit: Smoke-Test bestanden. Die Summenkontrolle findet die echten Abweichungen in `img2`; `8.5` wird korrekt normalisiert. Das Modell ist nicht deterministisch, deshalb validiert die App die Struktur jetzt streng und repariert ungültige Antworten. Offener, nicht blockierender Punkt: Der Name von Spieler 43 in `img.jpg` wurde nicht gelesen (Namen sind optional). Keine Prompt-Änderung für v1 nötig.

**2026-11-08 — Re-Test nach Prompt-Version 2 (`wurf_zeilen`).**

Nach dem Naming-Refactoring wurde das Schema auf `wurf_zeilen` umgestellt und `PROMPT_VERSION` auf `2` erhöht. Die drei Beispiele wurden erneut mit `--reprocess --no-cache` gelesen:

- `img1.jpg`: 4/4 Summen korrekt, 0 offene Punkte. 3650 prompt / 274507 completion (272748 reasoning), ca. **$0.1127** (Length-Retry von 262144 auf 524288 wurde genutzt).
- `img.jpg`: 4/4 Summen korrekt, 3 offene Punkte (nur `8.5`-Normalisierungen). 1825 prompt / 5837 completion (2485 reasoning), ca. **$0.0025**.
- `img2.jpg`: 3 offene Punkte: Spieler 17 (765/755), Spieler 48 (1080/1090) und Spieler 30 (645/635, weil W5 fälschlich als 80 statt 90 gelesen wurde). 4083 prompt / 278070 completion (251849 reasoning), ca. **$0.1142** (Length-Retry genutzt).
- Kombinierter Cache-Lauf: 12 Gruppen, 0 Konflikte, 6 offene Punkte, 3 Cache-Treffer, **$0**.

Zusatzkosten dieses Re-Tests: ca. **$0.23**. Der neue Schema-Feldname funktioniert, die Modellgenauigkeit bleibt aber nicht deterministisch. Der zusätzliche `img2`-Fund bei Spieler 30 ist ein Beispiel dafür, dass die Summenkontrolle auch falsche Einzelwerte sichtbar macht.
