# 14: CSV-Altpfad entfernen und Dokumentation angleichen

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Contract-Hälfte des Expand-Contract: Nachdem der SQLite-/Web-Pfad vollständig läuft, verschwinden der CSV-Store, die Aufräumlogik, der alte Pipeline-Pfad und das `review/`-Verhalten. Tests und Dokumentation beschreiben nur noch SQLite, Scan-Archiv und Web-UI.

**Blocked by:** 01–13 und 15

**Status:** resolved

- [x] Kein Laufzeitpfad liest oder schreibt noch `auswertung.csv`.
- [x] Es gibt kein Aufräumen mehr, das Scans löscht oder nach `review/` verschiebt.
- [x] Der alte Pipeline- und CSV-spezifische Code ist entfernt; es bleiben keine toten Referenzen.
- [x] CSV-spezifische Tests sind entfernt oder auf den SQLite-Pfad übertragen; die volle Suite ist grün.
- [x] README, Spec, AGENTS und Coding Standards beschreiben SQLite und die Web-UI statt CSV.
- [x] `knobeln` und `knobeln import` arbeiten ausschließlich mit SQLite und dem Scan-Archiv.
