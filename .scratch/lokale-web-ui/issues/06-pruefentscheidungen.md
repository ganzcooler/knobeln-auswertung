# 06: Prüfentscheidungen

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Turnierleitung entscheidet einen Prüffall direkt in der Prüfen-Ansicht: Vorschlag übernehmen, Wert korrigieren oder Zelle als unleserlich markieren. Die Entscheidung wird sofort gespeichert, die Werte und Status werden neu berechnet, und der nächste Fall wird ausgewählt. Ein Toast bestätigt „Gespeichert“ und erlaubt das Rückgängigmachen der letzten Korrektur.

**Blocked by:** 05 — Prüf-Queue und Bogen-Detail

**Status:** ready-for-agent

- [ ] „Übernehmen“, „Korrigieren“ und „Unleserlich“ aktualisieren den zugrunde liegenden Zellwert und die Status-Codes.
- [ ] Nach einer Entscheidung sinkt der Queue-Zähler; der nächste offene Fall wird ausgewählt.
- [ ] Die Entscheidung wird sofort gespeichert; bei einem Speicherfehler bleibt sie sichtbar und kann erneut versucht werden.
- [ ] Ein Toast „Gespeichert“ bietet „Rückgängig“ für die letzte Korrektur.
- [ ] Der Rohwert bleibt nach einer Korrektur sichtbar.
- [ ] „Bogen bestätigen“ ist nur möglich, wenn keine offenen Prüffälle mehr existieren.
- [ ] Tests am Anwendungskern und an der HTTP-Fläche decken alle drei Aktionen, Neuberechnung, Undo und Speicherfehler ab.
