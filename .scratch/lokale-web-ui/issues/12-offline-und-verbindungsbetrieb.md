# 12: Offline- und Verbindungsbetrieb

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Web-App startet und funktioniert ohne Internet und ohne API-Key. Nur die Extraktion braucht den LLM-Dienst. Die UI zeigt den Verbindungsstatus, bietet „Erneut prüfen“ und lässt Uploads warten, bis der Dienst wieder erreichbar ist. Prüfen, manuelle Erfassung, Rangliste, Abschluss und XLSX-Export funktionieren vollständig lokal.

**Blocked by:** 04 — Scan wird gelesen: Hintergrund-Extraktion; 07 — Manuelle Durchgangsergebnisse; 09 — Rangliste und Gesamtwertung; 10 — Durchgang abschließen und wieder öffnen

**Status:** resolved

- [x] Die App startet ohne API-Key und ohne Internet; vorhandene Turniere und Ergebnisse bleiben sichtbar.
- [x] Die Statusanzeige zeigt „Dienst erreichbar“, „Dienst nicht erreichbar“ oder „Status unbekannt“ mit „Erneut prüfen“.
- [x] Uploads werden angenommen und warten; nach Wiederherstellung der Verbindung werden sie erneut versucht.
- [x] Prüfen, manuelle Erfassung, Rangliste, Abschluss und XLSX-Export funktionieren offline.
- [x] Ein fehlschlagender LLM-Aufruf blockiert keine lokale Ansicht und keinen lokalen Speichervorgang.
- [x] Tests mit einem fehlschlagenden Fake-LLM decken Start, Status, wartende Jobs und lokale Bedienbarkeit ab.
