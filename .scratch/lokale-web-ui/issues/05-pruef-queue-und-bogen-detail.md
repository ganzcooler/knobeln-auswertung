# 05: Prüf-Queue und Bogen-Detail

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Prüfen-Ansicht zeigt eine nach Schweregrad sortierte Queue der offenen Prüffälle und den ausgewählten Bogen mit ganzem Scan, Zoom/Pan, Wertetabelle und Summencheck. Ein Bogen ohne Auffälligkeiten lässt sich in einem Klick bestätigen.

**Blocked by:** 04 — Scan wird gelesen: Hintergrund-Extraktion

**Status:** ready-for-agent

- [ ] Prüffälle werden aus Status-Codes und LLM-Hinweisen abgeleitet; die Queue ist nach Schweregrad sortiert und filterbar.
- [ ] Der erste offene Fall ist ausgewählt; ohne offene Fälle erscheint ein Leerzustand mit dem nächsten Schritt.
- [ ] Das Bogen-Detail zeigt den ganzen Scan mit Zoom und Pan, die Wertetabelle und den Summencheck.
- [ ] Rohwert, erkannter Wert, Vorschlag und zulässige Werte sind unterscheidbar.
- [ ] Ein Bogen ohne offene Prüffälle lässt sich in einem Klick bestätigen; saubere Bögen werden nicht automatisch bestätigt.
- [ ] Tests am Anwendungskern und an der HTTP-Fläche decken Ableitung, Sortierung, Auswahl und Bestätigen ab.
