# 10: Durchgang abschließen und wieder öffnen

**Spec:** [../spec.md](../spec.md)

**What to build:** Ein Durchgang lässt sich abschließen, sobald keine offenen Prüffälle mehr existieren. Danach ist er gesperrt, die Rangliste ist bestätigt und neue Scans werden abgelehnt. Zum Korrigieren lässt er sich mit Bestätigung wieder öffnen; vorher entsteht eine SQLite-Kopie.

**Blocked by:** 06 — Prüfentscheidungen; 09 — Rangliste und Gesamtwertung

**Status:** ready-for-agent

- [ ] „Durchgang abschließen“ ist bei offenen Prüffällen blockiert und nennt den Grund.
- [ ] Ein abgeschlossener Durchgang ist gesperrt; neue Scans für ihn werden abgelehnt.
- [ ] Die Rangliste zeigt danach „Bestätigt“.
- [ ] „Wieder öffnen“ verlangt eine Bestätigung und legt vorher eine SQLite-Kopie an.
- [ ] Nach dem Wiederöffnen sind Prüfungen und neue Scans wieder möglich.
- [ ] Tests am Anwendungskern und an der HTTP-Fläche decken Blockade, Abschließen, Sperre, Wiederöffnen und Backup ab.
