# 07: Manuelle Durchgangsergebnisse

**Spec:** [../spec.md](../spec.md) · **ADR:** [0004](../../../docs/adr/0004-manual-results.md)

**What to build:** Wenn keine brauchbare Extraktion möglich ist, erfasst die Turnierleitung pro Spieler und Durchgang eine Summe in einer einfachen Tabelle. Das Ergebnis wird als Durchgangsergebnis gespeichert, sichtbar als „manuell“ markiert, gegen 0–2400 und die 5er-Regel geprüft und für Rangliste und Abschluss verwendet. Es funktioniert ohne Netz und ohne API-Key.

**Blocked by:** 02 — Durchgang anlegen und auswählen

**Status:** ready-for-agent

- [ ] Eine Tabelle mit „+ Spieler“ erfasst Spieler-Nr. (Pflicht), optionalen Namen und eine Summe.
- [ ] Ungültige Summen (außerhalb 0–2400 oder nicht durch 5 teilbar) werden inline abgelehnt.
- [ ] Das Ergebnis wird als Durchgangsergebnis mit Quelle „manuell“ gespeichert und ist im Durchgang sichtbar.
- [ ] Manuelle Ergebnisse zählen für Rangliste und Abschluss und sind vor dem Abschluss bearbeitbar.
- [ ] Manuelle Ergebnisse sind keine Prüffälle, solange die Summe gültig ist.
- [ ] Die Erfassung funktioniert ohne API-Key und ohne Netz.
- [ ] Tests am Anwendungskern und an der HTTP-Fläche decken Anlegen, Validierung, Bearbeiten und Offline-Fall ab.
