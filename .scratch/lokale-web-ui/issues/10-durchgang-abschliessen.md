# 10: Durchgang abschließen und wieder öffnen

**Spec:** [../spec.md](../spec.md)

**What to build:** Ein Durchgang lässt sich abschließen, sobald keine offenen Prüffälle mehr existieren. Danach ist er gesperrt, die Rangliste ist bestätigt und neue Scans werden abgelehnt. Zum Korrigieren lässt er sich mit Bestätigung wieder öffnen; vorher entsteht eine SQLite-Kopie.

**Blocked by:** 06 — Prüfentscheidungen; 09 — Rangliste und Gesamtwertung

**Status:** resolved

- [x] „Durchgang abschließen“ ist bei offenen Prüffällen blockiert und nennt den Grund.
- [x] Ein abgeschlossener Durchgang ist gesperrt; neue Scans für ihn werden abgelehnt.
- [x] Die Rangliste zeigt danach „Bestätigt“.
- [x] „Wieder öffnen“ verlangt eine Bestätigung und legt vorher eine SQLite-Kopie an.
- [x] Nach dem Wiederöffnen sind Prüfungen und neue Scans wieder möglich.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken Blockade, Abschließen, Sperre, Wiederöffnen und Backup ab.
