# 09: Rangliste und Gesamtwertung

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Rangliste zeigt pro Durchgang und als Gesamtwertung alle Ergebnisse, getrennt nach gescannt und manuell. Die Gesamtwertung ist die Summe aller Durchgänge; Gleichstand erzeugt denselben Rang. Der Status „vorläufig“ oder „bestätigt“ ist sichtbar, ebenso ein Vollbild für den Beamer.

**Blocked by:** 08 — Konflikt-Ansicht

**Status:** resolved

- [x] Die Durchgangsrangliste sortiert nach Ergebnis und zeigt geteilten Rang bei Gleichstand.
- [x] Die Gesamtrangliste summiert alle Durchgänge eines Spielers im Turnier; Best-of und Durchschnitt gibt es nicht.
- [x] Der Status „vorläufig“ oder „bestätigt“ steht über der Tabelle und verlinkt offene Prüffälle.
- [x] Die Quelle „gescannt“ oder „manuell“ ist pro Ergebnis sichtbar.
- [x] Die Vollbild-Rangliste funktioniert und ist aus einiger Entfernung lesbar.
- [x] Ohne bestätigte Ergebnisse erscheint ein Leerzustand mit „Zu den Prüfungen“.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken Sortierung, Gleichstand, Gesamtsumme, Status und Leerzustand ab.
