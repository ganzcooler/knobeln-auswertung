# 03: Scans importieren und im Stapel sehen

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Turnierleitung legt JPG-, PNG- und PDF-Dateien per Drag-and-drop oder Dateiauswahl in den aktuellen Durchgang. Die Scans landen dauerhaft im Scan-Archiv, werden als Bögen erfasst und erscheinen mit Status „warten“ im Stapel. Doppelte Scans werden erkannt; nichts wird nach dem Import gelöscht.

**Blocked by:** 02 — Durchgang anlegen und auswählen

**Status:** resolved

- [x] Drag-and-drop und Dateiauswahl akzeptieren JPG, PNG und PDF.
- [x] PDF-Seiten werden als einzelne Bögen erfasst.
- [x] Die Original-Scans liegen dauerhaft im Scan-Archiv; die Datenbank referenziert sie.
- [x] Der Stapel zeigt pro Bogen Dateiname, Seite, Durchgang und Status „warten“.
- [x] Ein doppelter Scan wird erkannt; die Turnierleitung entscheidet über Behalten oder Ignorieren.
- [x] Eine nicht unterstützte oder fehlerhafte Datei wird inline gemeldet; die übrigen Uploads laufen weiter.
- [x] Tests am Anwendungskern und an der HTTP-Fläche decken Upload, PDF-Mehrseiter, Duplikat und Fehlerfall ab.
