# 15: Hilfe, Tastatur und Accessibility-Polish

**Spec:** [../spec.md](../spec.md)

**What to build:** Die Turnierleitung findet sich nach einer Pause ohne Schulung zurecht: ein Hilfe-Dialog erklärt die drei Schritte, zeigt die Tastenkürzel und den Verbindungsstatus. Die Prüf-Queue ist vollständig per Tastatur bedienbar, die aktuelle Auswahl wird per `aria-live` angekündigt, und die UI erfüllt die Accessibility-Grundlagen aus der Spec.

**Blocked by:** 06 — Prüfentscheidungen; 09 — Rangliste und Gesamtwertung; 10 — Durchgang abschließen und wieder öffnen; 12 — Offline- und Verbindungsbetrieb

**Status:** resolved

- [x] Ein Hilfe-Dialog öffnet mit `?`, schließt mit `Esc` und zeigt drei Schritte, Tastenkürzel und Verbindungsstatus.
- [x] Die Prüf-Queue ist vollständig per Tastatur bedienbar; die aktuelle Auswahl wird per `aria-live` angekündigt.
- [x] Fokus ist sichtbar; Ziele sind mindestens 44 × 44 px; es gibt keine Icon-only-Buttons ohne Label.
- [x] Status wird immer über Text plus Farbe gezeigt.
- [x] Die App bleibt bei 200-%-Zoom und in einem schmalen Tablet-Browserfenster benutzbar.
- [x] `prefers-reduced-motion` wird respektiert; es gibt keine Pflichtanimation.
- [x] Ein Accessibility-Durchgang ist dokumentiert; die relevanten Punkte sind durch Tests oder einen Smoke-Check abgedeckt.
