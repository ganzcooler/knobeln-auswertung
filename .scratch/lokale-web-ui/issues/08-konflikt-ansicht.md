# 08: Konflikt-Ansicht

**Spec:** [../spec.md](../spec.md) · **ADR:** [0004](../../../docs/adr/0004-manual-results.md)

**What to build:** Zwei Erfassungen desselben Spielers im selben Durchgang mit unterschiedlichen Ergebnissen werden als Konflikt angezeigt. Beide bleiben erhalten; die Turnierleitung sieht sie nebeneinander und wählt eine aus. Die andere wird als „verworfen“ markiert, nicht gelöscht. Die Rangliste verwendet genau eine Erfassung; ein offener Konflikt blockiert den Abschluss.

**Blocked by:** 06 — Prüfentscheidungen; 07 — Manuelle Durchgangsergebnisse

**Status:** resolved

- [x] Ein Konflikt entsteht bei gleichem Spieler und Durchgang mit unterschiedlichen Ergebnissen, sowohl Scan-gegen-Scan als auch Manuell-gegen-Scan.
- [x] Die Konflikt-Ansicht zeigt beide Erfassungen nebeneinander: Bogen, Werte, Summe und Status.
- [x] Die Turnierleitung wählt eine Erfassung; die andere wird als „verworfen“ markiert, bleibt sichtbar und wird nicht gelöscht.
- [x] Die Rangliste verwendet nur die gewählte Erfassung.
- [x] Ein offener Konflikt erscheint als Prüffall und blockiert „Durchgang abschließen“.
- [x] Ein späterer abweichender Scan öffnet einen geprüften Konflikt wieder.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken beide Konfliktarten, Auswahl, Verwerfen und Wiederöffnen ab.
