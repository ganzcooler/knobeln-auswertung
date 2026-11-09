# 02: Durchgang anlegen und auswählen

**Spec:** [../spec.md](../spec.md)

**What to build:** Ein Turnier lässt sich in die Durchgänge 1–5 gliedern. Die Turnierleitung legt einen Durchgang an, wählt ihn in der Top-Bar aus und sieht, ob er offen oder abgeschlossen ist. Ohne Durchgang erscheint ein klarer Leerzustand mit dem nächsten Schritt.

**Blocked by:** 01 — Turnier anlegen und lokale Web-App starten

**Status:** resolved

- [x] Ein Turnier kann die Durchgänge 1–5 enthalten; ein Durchgang lässt sich anlegen und auswählen.
- [x] Die Top-Bar zeigt das aktuelle Turnier und die Durchgangsauswahl.
- [x] Der Status „offen“ oder „abgeschlossen“ ist pro Durchgang sichtbar.
- [x] Ohne Durchgang erscheint ein Leerzustand mit CTA „Durchgang anlegen“.
- [x] Ein Fortschrittsplatzhalter („0 von 0 Bögen“) ist sichtbar und wird in späteren Tickets gefüllt.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken Anlegen, Auswählen und Leerzustand ab.
