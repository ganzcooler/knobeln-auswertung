# 09: Rangliste und Gesamtwertung

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Rangliste zeigt pro Durchgang und als Gesamtwertung alle Ergebnisse, getrennt nach gescannt und manuell. Die Gesamtwertung ist die Summe aller Durchgänge; Gleichstand erzeugt denselben Rang. Der Status „vorläufig“ oder „bestätigt“ ist sichtbar, ebenso ein Vollbild für den Beamer.

**Blocked by:** 08 — Konflikt-Ansicht

**Status:** ready-for-agent

- [ ] Die Durchgangsrangliste sortiert nach Ergebnis und zeigt geteilten Rang bei Gleichstand.
- [ ] Die Gesamtrangliste summiert alle Durchgänge eines Spielers im Turnier; Best-of und Durchschnitt gibt es nicht.
- [ ] Der Status „vorläufig“ oder „bestätigt“ steht über der Tabelle und verlinkt offene Prüffälle.
- [ ] Die Quelle „gescannt“ oder „manuell“ ist pro Ergebnis sichtbar.
- [ ] Die Vollbild-Rangliste funktioniert und ist aus einiger Entfernung lesbar.
- [ ] Ohne bestätigte Ergebnisse erscheint ein Leerzustand mit „Zu den Prüfungen“.
- [ ] Tests am Anwendungskern und an der HTTP-Fläche decken Sortierung, Gleichstand, Gesamtsumme, Status und Leerzustand ab.
