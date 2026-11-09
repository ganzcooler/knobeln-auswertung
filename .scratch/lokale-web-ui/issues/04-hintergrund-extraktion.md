# 04: Scan wird gelesen: Hintergrund-Extraktion

**Spec:** [../spec.md](../spec.md)

**What to build:** Ein importierter Scan wird als Hintergrundjob gelesen. Die UI zeigt den Job-Status (`warten`, `läuft`, `fertig`, `Fehler`) und später die erkannten Werte des Bogens. Fehlende Verbindung oder fehlender API-Key lassen den Job warten, ohne die App zu blockieren. Retry, Tokenverbrauch, Kosten und Cache sind sichtbar beziehungsweise wirksam.

**Blocked by:** 03 — Scans importieren und im Stapel sehen

**Status:** resolved

- [x] Ein Upload erzeugt einen Job; der Worker verarbeitet Jobs standardmäßig sequenziell.
- [x] Ein erfolgreicher Job speichert vier Spieler mit je zwölf Wurf-Zeilen, Summenzeile und Status; der Bogen ist sichtbar.
- [x] Ein Fehler setzt den Job auf „Fehler“ und bietet „Erneut versuchen“.
- [x] Ohne Netz oder API-Key bleibt der Job „warten“; Prüfen, manuelle Erfassung und Rangliste bleiben bedienbar.
- [x] Tokenverbrauch und geschätzte Kosten werden pro Extraktion gespeichert und angezeigt; `--max-cost` stoppt weitere Extraktion.
- [x] Das Schließen des Browsers unterbricht den Server-Job nicht; nach einem Server-Neustart werden offene Jobs wieder aufgenommen.
- [x] Tests mit Fake-LLM decken Erfolg, Fehler, Retry, Cache und Kostenlimit ab; der echte Modelltest bleibt manuell.
