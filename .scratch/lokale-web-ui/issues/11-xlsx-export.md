# 11: XLSX-Export

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Rangliste lässt sich auf Knopfdruck als XLSX exportieren. Die Datei enthält ein Blatt pro Durchgang plus ein Gesamtblatt; Quelle „gescannt“/„manuell“ und Status sind sichtbar. Bei einem Exportfehler bleibt die Rangliste stehen und der Export kann erneut versucht werden.

**Blocked by:** 09 — Rangliste und Gesamtwertung

**Status:** resolved

- [x] Ein Export erzeugt eine XLSX-Datei mit einem Blatt pro Durchgang und einem Gesamtblatt.
- [x] Die Blätter enthalten Rang, Spieler-Nr., Name, Ergebnisse, Quelle und Status.
- [x] Manuelle Ergebnisse sind im Export als „manuell“ erkennbar.
- [x] Ein Exportfehler zeigt eine klare Meldung mit „Erneut versuchen“; die Rangliste bleibt sichtbar.
- [x] Tests am Anwendungskern öffnen die erzeugte Arbeitsmappe und prüfen Blätter, Werte und Quellen.
