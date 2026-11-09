---
name: Knobeln-Auswertung
status: final
sources:
  - '{output_folder}/brainstorming/brainstorm-knobeln-workflow-2026-11-09/brainstorm.html'
  - '{output_folder}/brainstorming/brainstorm-knobeln-workflow-2026-11-09/.memlog.md'
  - '{output_folder}/planning-artifacts/ux-designs/ux-knobeln-idee-2026-11-09/.memlog.md'
updated: 2026-11-09
---

# Knobeln-Auswertung — Experience Spine

## Foundation

Lokale Web-App, Laptop-first, responsive bis Tablet. Python + SQLite; die Anwendung läuft auf `localhost`, Scans und Datenbank bleiben auf dem Rechner. Nur die Extraktion braucht eine Verbindung zum LLM-Dienst. Ein Arbeitsplatz: ein bis zwei Turnierleiter teilen sich den Laptop; kein Login, keine Rollen, keine Mehrbenutzer-Synchronisation. Sprache: Deutsch. Drei Sichten: **Scannen**, **Prüfen**, **Rangliste**. `DESIGN.md` ist die visuelle Identität; diese Spine beschreibt das Verhalten.

Die Anwendung ist eine **Werkbank für einen Abend im Jahr**. Sie muss nach zwölf Monaten Pause ohne Schulung verständlich sein. Deshalb ist die Top-Bar dauerhaft sichtbar, jeder Zustand erklärt den nächsten Schritt, und die drei Sichten sind zugleich die drei Stationen des Arbeitsablaufs.

Leitprinzip: **Review by Exception**. Nur Fälle, die die Prüfung nicht bestehen, werden zu Prüffällen. Die Summe ist Kontrolle, nie Quelle. Der Mensch entscheidet dort, wo die Maschine unsicher ist – nicht überall. Es gibt keinen formalen Audit-Trail und keine Prüfer-Identität; Rohwert, Vorschlag und korrigierter Wert bleiben trotzdem sichtbar.

## Scan-Geometrie

Die Zellgeometrie wird **deterministisch** aus dem Scan ermittelt, nicht vom LLM. Die Rastererkennung findet die Tabelle (Linien, Konturen, Perspektivkorrektur) und berechnet das Raster aus 4 Spieler-Spalten × 12 Wurf-Zeilen plus Kopf- und Summenzeile. Jede Zelle erhält eine `grid_position` (Spalte, Zeile) und ein Rechteck im Originalbild. Das LLM liefert ausschließlich Inhalt – Werte, Summe, Kopfzeilentext – und keine Koordinaten. Das hält die API-Kosten niedrig und die Geometrie reproduzierbar.

Der Cell-Inspector nutzt das Rechteck als Lupe auf den Original-Scan, nicht als separate Bilddatei. Schlägt die Rastererkennung fehl, kalibriert die Turnierleitung die vier Ecken der Tabelle manuell; scheitert auch das, wird der Bogen als „Geometrie unklar“ markiert und im Review als Ganzes mit Markierung gezeigt. Es gibt keine LLM-Bounding-Boxen.

## Information Architecture

| Surface | Reached from | Purpose |
|---|---|---|
| **Scannen** | App-Start / Tab | Bögen importieren, Stapel und Durchgangsfortschritt sehen |
| **Prüfen** | Tab / CTA „Weiter zum Prüfen“ | Offene Prüffälle entscheiden, Bögen bestätigen, Durchgang abschließen |
| **Rangliste** | Tab / CTA „Rangliste anzeigen“ | Durchgangs- und Gesamtrangliste, Status, Export, Vollbild |
| **Bogen-Detail** | Sheet-Card / Prüffall | Einzelner Bogen mit Bild, Werten und Summencheck |
| **Konflikt-Ansicht** | Prüffall „Konflikt“ | Zwei Erfassungen desselben Spielers vergleichen und eine wählen |
| **Durchgangsauswahl** | Top-Bar | Durchgang anlegen, auswählen, abschließen |
| **Hilfe** | Top-Bar | Kurzanleitung, Tastenkürzel, Verbindungsstatus |

Kein Dashboard, keine Einstellungsseite, kein Login. Die drei Tabs sind der gesamte Arbeitsbereich; alles andere ist ein Dialog oder eine Detailansicht innerhalb einer der drei Sichten.

Die Top-Bar enthält: Produktname, Durchgangsauswahl, die drei Tabs mit Zahlen (Anzahl Bögen, offene Prüfungen, „vorläufig“) und einen Hilfe-Link. Eine Zahl ist immer eine Zahl plus Text, nie nur ein Punkt.

Mockups und Wireframes sind illustrativ; bei Widersprüchen gewinnen die Spines: **Spines win on conflict** — die Spines sind der Vertrag.

Kompositionsreferenzen: [Scannen](mockups/scannen.html) zeigt Drop-Zone und Stapel; [Prüfen](mockups/pruefen.html) zeigt Queue, Cell-Inspector und Summencheck; [Rangliste](mockups/rangliste.html) zeigt Tabelle und Vollbild; [Konflikt](mockups/konflikt.html) zeigt die Zwei-Erfassungen-Ansicht.

## Voice and Tone

Neutrale, direkte Ansprache. Kurze Sätze. Keine Ausrufezeichen, keine Entwicklerbegriffe, keine Schuldzuweisungen. Die UI sagt, was passiert ist, was sie vorschlägt und was der Mensch tun kann.

| Do | Don't |
|---|---|
| „Bogen erkannt. 4 Spieler, 12 Würfe, Summe gefunden.“ | „OCR completed successfully.“ |
| „Summe stimmt nicht: 755 berechnet, 765 geschrieben.“ | „Validation error: sum mismatch.“ |
| „Dieser Wert steht nicht in der Wertung.“ | „Invalid enum value.“ |
| „Runde 1 ist noch nicht fertig. 3 offene Prüfungen.“ | „3 unresolved issues.“ |
| „Alles geprüft. Runde abschließen?“ | „Proceed to finalization.“ |
| „Der Dienst ist gerade nicht erreichbar. Die Bögen bleiben im Stapel.“ | „API error 503.“ |
| „Vorläufig“ / „Bestätigt“ | „Provisional“ / „Final“ ohne Erklärung |
| „Bitte den Ausschnitt mit dem Original vergleichen.“ | „Confidence score: 0.62.“ |

## Component Patterns

Behavioral. Visuelle Specs stehen in `DESIGN.md.Components`.

| Component | Use | Behavioral rules |
|---|---|---|
| **Top-Bar** | Global | Sticky, maximal 64 px. Produktname, Durchgangsauswahl, drei Tabs mit Zahlen, Hilfe. Verdeckt nie Inhalt; Tab-Wechsel erhält den Zustand der Sicht. |
| **Tab** | Global | Wechselt Scannen / Prüfen / Rangliste. Aktiver Tab unterstrichen; Zähler = Zahl + Text. Tastatur: Fokuswechsel per Tastatur, Enter/Space aktiviert. |
| **Round-Header** | Top-Bar | Zeigt Durchgangsauswahl, Fortschritt („12 von 16 Bögen“) und „Runde abschließen“. Abschließen ist deaktiviert, solange offene Prüfungen existieren, mit sichtbarem Grund. |
| **Drop-Zone** | Scannen | Akzeptiert JPG, PNG und PDF. Drag-and-drop oder „Dateien auswählen“. Pro Datei ein Fortschritt; Fehler inline. Doppelte Datei → Hinweis, nicht automatisch verwerfen. Bleibt während des Imports für weitere Dateien offen. |
| **Sheet-Card** | Scannen, Bogen-Detail | Vorschaubild, Dateiname, Durchgang, Spielerzahl, Status. Klick öffnet den Bogen. „Erneut lesen“ nur bei Fehlern. Zeigt offene Prüfungen pro Bogen. |
| **Review-Queue** | Prüfen | Sortiert nach Schweregrad: Summenfehler → unzulässiger Wert → unklare Ziffer → Konflikt → Kopfzeile. Filter „Alle / Summe / Unzulässig / Unklar / Konflikt“. Der erste Fall ist ausgewählt; die Auswahl bleibt beim Scrollen sichtbar. Leerer Zustand, wenn keine Fälle offen sind. |
| **Review-Queue-Item** | Prüfen | Links ein farbiger Rand nach Schweregrad, oben Spieler und Wurf, darunter Rohwert und Vorschlag, rechts ein Status-Badge. Klick oder Enter wählt aus; entscheidet nicht. Ausgewählt: blaue Fläche. |
| **Cell-Inspector** | Prüfen, Bogen-Detail | Großer Ausschnitt der Zelle als Lupe auf den Original-Scan; die Zellkoordinaten kommen aus der deterministischen Rastererkennung, nicht aus dem LLM. Zoom und Pan; etwas Umgebung bleibt sichtbar. Zeigt „Erkannt“, „Vorschlag“ und die zulässigen Werte. Aktionen: „Übernehmen“, „Korrigieren“, „Unleserlich“, immer sichtbar. Der Rohwert bleibt sichtbar. Bild fehlt: Dateiname und „Erneut lesen“. |
| **Sum-Check** | Prüfen, Bogen-Detail | Zeigt berechnete und geschriebene Summe in `{typography.number-lg.fontSize}`, dazu die Differenz. Listet Zellen, die den Unterschied erklären könnten. Ändert nie automatisch einen Wert. Bei Übereinstimmung ist „Summe stimmt“ eine Kontrolle, keine automatische Freigabe. |
| **Sheet-Review** | Bogen-Detail | 4 Spieler × 12 Würfe als Tabelle; jede Zelle mit Rohwert und Status. Saubere Bögen: „Bogen bestätigen“ in einem Klick. Offene Zellen öffnen den Cell-Inspector. Bestätigte Zellen sind gesperrt; der Rohwert bleibt sichtbar. |
| **Conflict-View** | Konflikt-Ansicht | Zwei Erfassungen nebeneinander: Bogen, Werte, Summe, Status. Aktion „Diese Erfassung gilt“; die andere wird als „verworfen“ markiert, nicht gelöscht. Erfordert eine ausdrückliche Wahl. Fehlt eine Erfassung: „Scan fehlt“ + „Erneut lesen“; die Wahl bleibt blockiert, bis beide Seiten sichtbar sind. |
| **Leaderboard Table** | Rangliste | Umschalter „Durchgang“ / „Gesamt“. Spalten: Rang, Spieler-Nr., Name, Durchgänge, Summe, Status. Sortierung nach Summe; Gleichstand wird als „geteilter Rang“ gezeigt. Kopfzeile bleibt stehen. Vollbild skaliert hoch. Leerer Zustand, wenn keine bestätigten Ergebnisse vorliegen. |
| **Status-Badge** | Überall | `{components.status-confirmed}`, `{components.status-provisional}`, `{components.status-open}`. Immer Text plus Farbe, nie nur Farbe. Deutsche Beschriftung. |
| **Primary Button** | Überall | Genau eine primäre Aktion pro Zustand. Vorwärtsaktionen: „Weiter zum Prüfen“, „Bogen bestätigen“, „Runde abschließen“. Deaktiviert nur mit genanntem Grund. |
| **Secondary Button** | Überall | Für „Abbrechen“, „Später“, „Exportieren“, „Vollbild“. Konkurriert nie mit der primären Aktion. |
| **Number Cell** | Tabellen | Rechtsbündig, tabellarisch. Klick öffnet den Cell-Inspector. Zeigt Rohwert und korrigierten Wert unterscheidbar; versteckt den Rohwert nie. |
| **Help-Dialog** | Hilfe | Drei Schritte, Tastenkürzel, Verbindungsstatus. Keine technische Dokumentation. Öffnet mit `?`, schließt mit Esc. |
| **Toast** | Global | Kurze Bestätigung „Gespeichert“; „Rückgängig“ für die letzte Korrektur; Offline-Hinweis. Nur ein Toast gleichzeitig. Verdeckt nie die aktive Zelle oder die primäre Aktion. Speicherfehler bleiben mit Retry stehen. |
| **Status-Banner** | Rangliste, Prüfen, Scannen | Vorläufig: „Vorläufig – 3 offene Prüfungen“ + Link. Bestätigt: „Bestätigt“ + „Exportieren“ + „Vollbild“. Offline: „Der Dienst ist gerade nicht erreichbar.“ Verdeckt nie den Inhalt. |
| **Empty State** | Scannen, Prüfen, Rangliste, Bogen-Detail | Ein Satz, was passiert ist, ein Satz, was zu tun ist, genau eine primäre Aktion. Nie eine Sackgasse. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| **Erster Start** | Global | Dialog „Turnier anlegen“ oder „Letztes Turnier öffnen“. Das letzte Turnier wird gemerkt. |
| **Kaltstart / Laden** | Alle Flächen | Top-Bar sichtbar. Scannen: Drop-Zone-Skeleton; Prüfen: Queue-Skeleton mit „Prüffälle werden geladen …“; Rangliste: Tabellen-Skeleton mit „Rangliste wird berechnet …“; Bogen-Detail: Bild-Skeleton; Konflikt-Ansicht: beide Seiten als Skeleton; Durchgangsauswahl und Hilfe: Inhalte sofort, kein Netz nötig. Kein leerer Bildschirm. |
| **Laden fehlgeschlagen** | Alle Flächen | „Daten konnten nicht geladen werden. Erneut versuchen.“ Top-Bar bleibt sichtbar; keine leere Fläche. |
| **Speichern fehlgeschlagen** | Alle Flächen | Toast „Konnte nicht gespeichert werden. Erneut versuchen.“ Die Entscheidung bleibt in der UI; Retry ohne Neuauswahl. |
| **Keine Berechtigung** | Global | Nicht anwendbar: kein Login, keine Rollen, keine Mehrbenutzerverwaltung. |
| **Offline** | Alle Flächen | Prüfen, Rangliste und Export funktionieren lokal weiter. Nur neue Extraktion braucht den Dienst; Status in Top-Bar und Hilfe. |
| **Kein Durchgang** | Scannen | „Wähle oder lege einen Durchgang an.“ Drop-Zone bleibt sichtbar, aber inaktiv; CTA „Durchgang anlegen“. |
| **Keine Bögen** | Scannen | Drop-Zone mit „Noch keine Bögen. Lege die Scans hier ab.“ |
| **Drag-over / Fokus** | Scannen | Drop-Zone blau umrandet, Label „Zum Ablegen loslassen“. |
| **Import läuft** | Scannen | Pro Datei „Wird gelesen …“ mit Fortschritt. Die Drop-Zone bleibt für weitere Dateien offen. |
| **Bogen erkannt** | Scannen / Prüfen | Keine Auffälligkeiten: „Bogen erkannt. Keine Auffälligkeiten.“ + „Bogen bestätigen“. Mit Prüffällen: „Bogen erkannt. 2 Prüfungen.“ + Link „Prüfungen anzeigen“. Kein automatisches Bestätigen. |
| **Importfehler** | Scannen | „Datei konnte nicht gelesen werden. Bitte als JPG, PNG oder PDF erneut ablegen.“ Die Datei bleibt sichtbar, nichts geht verloren. |
| **Doppelter Scan** | Scannen | „Dieser Bogen scheint schon im Stapel zu sein.“ Aktionen „Behalten“ / „Ignorieren“. |
| **Dienst nicht erreichbar** | Scannen | „Der Dienst ist gerade nicht erreichbar. Die Bögen bleiben im Stapel.“ + „Erneut versuchen“. Review und Rangliste funktionieren weiter. |
| **Stapel vollständig** | Scannen | „16 von 16 Bögen erkannt · 7 offene Prüfungen“ + CTA „Weiter zum Prüfen“. |
| **Keine offenen Prüfungen** | Prüfen | „Alles geprüft. Keine offenen Fälle.“ + „Rangliste anzeigen“ und „Runde abschließen“. |
| **Offene Prüfungen** | Prüfen | „7 offene Prüfungen“ + Queue. Der erste Fall ist ausgewählt. |
| **Kein Fall ausgewählt** | Prüfen | Rechte Seite: „Wähle einen Prüffall aus der Queue.“ |
| **Ausschnitt lädt** | Prüfen | „Ausschnitt wird geladen …“; die Zelle bleibt markiert. |
| **Summe stimmt nicht** | Prüfen | „Summe stimmt nicht: 755 berechnet, 765 geschrieben. Delta 10.“ Die Kandidatenzellen sind markiert. |
| **Unzulässiger Wert** | Prüfen | „Dieser Wert steht nicht in der Wertung.“ Zulässige Werte als auswählbare Liste. |
| **Unklare Ziffer** | Prüfen | „80 oder 90?“ Großer Ausschnitt, beide Kandidaten, „Übernehmen“ pro Kandidat. |
| **Konflikt** | Prüfen | „Spieler 42 kommt auf zwei Bögen vor.“ Side-by-side; eine Erfassung wird gewählt, die andere verworfen. |
| **Kopfzeile unklar** | Prüfen | „Spieler-Nr. fehlt“ oder „Durchgang unklar“. Kopfzeilen-Ausschnitt + Eingabefeld. |
| **Geometrie unklar** | Prüfen, Bogen-Detail | „Die Tabelle konnte nicht erkannt werden.“ Aktionen „Ecken kalibrieren“ und „Ganzen Bogen prüfen“. Die Werte bleiben sichtbar; die Zellzuordnung ist manuell. |
| **Fall gespeichert** | Prüfen | Toast „Gespeichert“; der nächste Fall wird ausgewählt; der Queue-Zähler sinkt. |
| **Runde fertig** | Prüfen | „Alles geprüft. Runde abschließen?“ + CTA „Rangliste anzeigen“. |
| **Runde abgeschlossen** | Prüfen | „Runde abgeschlossen.“ Die Rangliste ist bestätigt; spätere Importe erzeugen eine neue Version. `[ASSUMPTION]` |
| **Keine Ergebnisse** | Rangliste | „Noch keine bestätigten Ergebnisse.“ + Link „Zu den Prüfungen“. |
| **Durchgang ohne Ergebnisse** | Rangliste | „Für diesen Durchgang gibt es noch keine bestätigten Ergebnisse.“ + Link „Zu den Prüfungen“. |
| **Rangliste vorläufig** | Rangliste | Status-Banner „Vorläufig – 3 offene Prüfungen“ + Link „Prüfungen anzeigen“. Die Tabelle bleibt sichtbar. |
| **Rangliste bestätigt** | Rangliste | Status-Banner „Bestätigt“ + „Exportieren“ + „Vollbild“. |
| **Gleichstand** | Rangliste | „Geteilter Rang“ in der Rangspalte; gleiche Summe, gleicher Rang. Die Rangfolge danach ist offen. `[ASSUMPTION]` |
| **Export läuft / Exportfehler** | Rangliste | „Export wird vorbereitet …“; bei Fehler „Export konnte nicht erstellt werden. Erneut versuchen.“ Die Tabelle bleibt sichtbar. |
| **Vollbild** | Rangliste | Die Tabelle nutzt die gesamte Fläche; Esc beendet; Namen und Summen größer. |
| **Bild fehlt / beschädigt** | Bogen-Detail, Prüfen | „Scan konnte nicht angezeigt werden.“ + Dateiname + „Erneut lesen“. Die Werte bleiben sichtbar. |
| **Keine Auffälligkeiten** | Bogen-Detail | „Keine Auffälligkeiten.“ + „Bogen bestätigen“. |
| **Offene Fälle** | Bogen-Detail | Liste der Prüffälle; betroffene Zellen markiert; Klick öffnet den Cell-Inspector. |
| **Bogen bestätigt** | Bogen-Detail | Status-Badge „Bestätigt“; Zellen gesperrt; Rohwerte bleiben sichtbar. |
| **Eine Erfassung fehlt** | Konflikt-Ansicht | „Scan fehlt“ + „Erneut lesen“; die Auswahl bleibt blockiert, bis beide Seiten sichtbar sind. |
| **Auswahl getroffen** | Konflikt-Ansicht | Gewählte Erfassung grün, andere „verworfen“; Toast „Gespeichert“ + „Rückgängig“. |
| **Keine Durchgänge** | Durchgangsauswahl | „Noch kein Durchgang. Lege den ersten an.“ Namensfeld + „Anlegen“. |
| **Anlegen / Validierungsfehler** | Durchgangsauswahl | Namensfeld; leerer oder doppelter Name → Inline-Fehler; „Anlegen“ erst bei gültigem Namen. |
| **Auswählen** | Durchgangsauswahl | Liste der Durchgänge mit Status; der aktuelle ist hervorgehoben. |
| **Abschließen blockiert** | Durchgangsauswahl | „Runde abschließen“ deaktiviert mit Grund „3 offene Prüfungen“. |
| **Inhalt** | Hilfe | Drei Schritte, Tastenkürzel, Verbindungsstatus. |
| **Verbindungsstatus** | Hilfe | „Dienst erreichbar“ / „Dienst nicht erreichbar“ / „Status unbekannt“ mit „Erneut prüfen“. Keine technischen Details. |

Konflikt-Ansicht und Hilfe haben keinen Leerzustand: Die Konflikt-Ansicht wird nur mit einem Konflikt geöffnet; die Hilfe hat immer Inhalt. Das Bogen-Detail hat keinen Leerzustand; ein Bogen ohne Auffälligkeiten ist der Zustand „Keine Auffälligkeiten“.

## Interaction Primitives

- **Maus und Touch sind der primäre Weg.** Große Ziele, sichtbare Labels, keine Hover-only-Aktionen.
- **Drag-and-drop** für Scans; Dateiauswahl als gleichwertiger Fallback.
- **Zoom und Pan** auf dem Scan, damit die Handschrift beurteilbar ist. Doppelklick zoomt auf die aktuelle Zelle.
- **Tastatur als Beschleuniger, nicht als Pflicht:** `A` übernehmen, `K` korrigieren, `U` unleserlich, `S` überspringen, `Enter` nächster Fall, `Esc` schließen, `?` Hilfe. Die Maus bleibt vollständig funktionsfähig.
- **Sofort speichern.** Jede Entscheidung wird direkt gespeichert; kein „Speichern“-Button. Ein kurzes „Gespeichert“ bestätigt.
- **Rückgängig** für die letzte Korrektur per Toast; keine mehrstufige Historie nötig.
- **Bestätigungen nur für destruktive Aktionen:** Bogen verwerfen, Runde abschließen, Turnier löschen. Normale Korrekturen brauchen keine Bestätigung.
- **Fokus bleibt im Prüffall.** Nach einer Entscheidung wird der nächste Fall ausgewählt, aber nie ohne sichtbare Bestätigung automatisch geöffnet.
- **Verboten:** Drag-to-Reorder, Rechtsklick-Menüs, unendliches Scrollen, Modal-Stapel über zwei Ebenen, Auto-Weiter nach einer Entscheidung ohne sichtbare Bestätigung.

## Accessibility Floor

- WCAG 2.2 AA für die lokale Web-App: Kontrast, Fokus, Tastaturbedienbarkeit, 200-%-Zoom.
- Status immer über Text plus Farbe; nie nur Rot/Grün.
- Jede Tabelle hat eine sichtbare Kopfzeile und Screenreader-Beschriftungen für Rang, Spieler und Summe.
- Die Review-Queue ist vollständig per Tastatur bedienbar; die aktuelle Auswahl wird per `aria-live` angekündigt.
- Ziele mindestens 44 × 44 px; keine Icon-only-Buttons ohne Label.
- Die Vollbild-Rangliste ist aus 3–5 Metern lesbar: große Summen, hoher Kontrast, keine dekorativen Details.
- Keine Zeitlimits, keine automatischen Weiterleitungen, keine Bewegung als Pflicht. `prefers-reduced-motion` wird respektiert.
- Kontrastziele: `{colors.ink}` auf `{colors.paper}` mindestens 7:1; `{colors.ink-soft}` auf `{colors.paper}` mindestens 4,5:1; `{colors.paper-raised}` auf `{colors.blue}` mindestens 4,5:1; Statusfarben auf ihren Washes mindestens 4,5:1. Fokusringe sind sichtbar und mindestens 3:1 gegen die Umgebung.

## Responsive & Platform

| Breakpoint | Behavior |
|---|---|
| **≥ 1280 px** | Prüfen: Queue links (360–420 px), Bogen und Inspektor rechts. Rangliste: volle Breite. |
| **1024–1279 px** | Prüfen: Queue schmaler, Bogen bleibt sichtbar. |
| **< 1024 px** | Prüfen: Queue und Detail stapeln; die Queue wird eine horizontale Liste. Scannen bleibt einspaltig. |
| **Vollbild** | Rangliste nutzt die gesamte Fläche; Namen in `{typography.heading.fontSize}`, Summen in `{typography.number-xl.fontSize}`. |

Laptop ist die primäre Plattform; Tablet ist sekundär für Scannen und Prüfen. Keine native Mobile-App, kein Dark Mode in v1. Ein Print-Stylesheet für Rangliste und Prüfprotokoll ist vorhanden.

## Inspiration & Anti-patterns

- **Inspiriert von Scanner-Software:** ein großer Einwurfbereich, klare Dateiliste, Fortschritt pro Datei.
- **Inspiriert von Tabellenkalkulation:** die Rangliste ist eine Tabelle, keine Kartenwand; Zahlen sind rechtsbündig und vergleichbar.
- **Inspiriert von Foto-Review-Werkzeugen:** großer Ausschnitt, Zoom, klares „Übernehmen“.
- **Inspiriert von einem Papier-Fahrtenbuch:** ruhige Flächen, klare Zeilen, keine Ablenkung.

**Abgelehnt:** Enterprise-Dashboard, Multi-Rollen-Admin, Login, Dark Mode, Gamification, KI-Chat, automatische Korrektur, versteckte Rohwerte, Icon-only-Buttons, Modal-Stapel, Infinite Scroll, Echtzeit-Kollaboration. Die Anwendung ist eine Werkbank für ein bis zwei Personen, keine Plattform.

## Key Flows

### Flow 1 — Der Stapel (Dano, Turnierleiter, 18:30, Vereinsheim)

1. Dano öffnet die App. Das letzte Turnier ist gemerkt; er legt „Durchgang 1“ an.
2. Er zieht 16 Scans in die Drop-Zone.
3. Die Liste zeigt pro Datei „Wird gelesen …“, dann „Erkannt“ oder „Prüfen (2)“.
4. Dano sieht: „12 von 16 Bögen erkannt · 7 offene Prüfungen“.
5. **Höhepunkt:** Er klickt „Weiter zum Prüfen“. Die Queue zeigt genau die sieben Fälle, die einen Menschen brauchen; der Rest ist schon erledigt. Dano weiß, wo er anfangen muss.

Fehlerfall: Eine Datei ist kein Bogen → „Datei konnte nicht gelesen werden. Bitte als JPG, PNG oder PDF erneut ablegen.“ Die Datei bleibt sichtbar, nichts geht verloren. Ist der Dienst nicht erreichbar → „Der Dienst ist gerade nicht erreichbar. Die Bögen bleiben im Stapel.“ + „Erneut versuchen“; Prüfen und Rangliste funktionieren weiter.

### Flow 2 — Die Summe passt nicht (Dano, Turnierleiter, 18:50)

1. Die Queue zeigt: „Spieler 42 · Wurf 12 · 100 oder 110 · Summe 755 vs. 765“.
2. Dano klickt den Fall. Der Scan zoomt auf die Zelle; der Ausschnitt zeigt „100“ mit einem langen Anstrich.
3. Der Sum-Check sagt: „Berechnet 755 · Geschrieben 765 · Delta 10.“ Die Kandidatenliste sagt: „110 würde die Summe treffen.“
4. Dano vergleicht den Ausschnitt, wählt „110“. Die Summe springt auf 765, der Fall verschwindet.
5. **Höhepunkt:** Die Korrektur bleibt als „100 → 110“ sichtbar. Die Summe war ein Hinweis, nicht die Entscheidung. Dano bestätigt den Bogen.

Fehlerfall: Dano wählt versehentlich den falschen Wert → „Rückgängig“ im Toast; der Fall kehrt in die Queue zurück. Schlägt das Speichern fehl → „Konnte nicht gespeichert werden. Erneut versuchen.“; der Fall bleibt ausgewählt.

### Flow 3 — Der zweite Bogen (Dano, Turnierleiter, 19:10)

1. Die Queue zeigt: „Spieler 42 kommt auf Bogen 3 und Bogen 7 vor.“
2. Die Konflikt-Ansicht zeigt beide Bögen nebeneinander: Werte, Summen, Status.
3. Dano erkennt am Bogen und an der Summe, welche Erfassung gilt; er wählt „Bogen 3 gilt“.
4. Bogen 7 wird als „verworfen“ markiert, bleibt aber im Stapel sichtbar.
5. **Höhepunkt:** Kein Wert wurde überschrieben. Die Rangliste verwendet genau eine Erfassung, und Dano kann erklären, warum.

Fehlerfall: Beide Erfassungen wirken plausibel → Dano lässt den Fall offen und prüft die Originale; der Konflikt bleibt in der Queue. Fehlt ein Scan → „Scan fehlt“ + „Erneut lesen“; die Wahl bleibt blockiert, bis beide Seiten sichtbar sind. Schlägt das Speichern fehl → die Auswahl bleibt sichtbar; Retry.

### Flow 4 — Die Rangliste (Dano, Turnierleiter, 20:00)

1. Dano öffnet „Rangliste“. Status-Banner: „Vorläufig – 2 offene Prüfungen.“
2. Er löst die letzten zwei Fälle; das Status-Banner wird „Bestätigt“.
3. Er klickt „Runde abschließen“. Die Rangliste ist final.
4. Er exportiert XLSX und öffnet „Vollbild“ für den Beamer.
5. **Höhepunkt:** Der Raum sieht eine klare, große Rangliste; Dano kann jede Zahl erklären, weil die Prüfentscheidung am Wert sichtbar ist.

Fehlerfall: Der Export schlägt fehl → „Export konnte nicht erstellt werden. Erneut versuchen.“ Die Tabelle bleibt sichtbar; Vollbild funktioniert weiter. Sind noch Prüfungen offen, ist „Runde abschließen“ deaktiviert und nennt den Grund; das Status-Banner bleibt „Vorläufig“.

### Flow 5 — Nächster Durchgang (Dano, Turnierleiter, 20:30)

1. Dano legt „Durchgang 2“ an.
2. Die drei Sichten bleiben gleich; die Durchgangsauswahl zeigt „Durchgang 1 · Durchgang 2 · Gesamt“.
3. Die Gesamtrangliste aggregiert beide Durchgänge.
4. **Höhepunkt:** Der Jahresablauf ist wiederholbar, ohne dass jemand eine Anleitung lesen muss.

Fehlerfall: Der Name existiert schon → Inline-Hinweis „Diesen Durchgang gibt es schon.“ Dano wählt einen anderen Namen oder öffnet den bestehenden Durchgang. Ist der neue Durchgang noch leer → „Noch keine Bögen. Lege die Scans hier ab.“

## Open Questions & Assumptions

**Bestätigte Leitplanken**

- **Kein Audit-Trail:** keine Prüfer-Identität, kein Revisionsbericht. Rohwert, Vorschlag und korrigierter Wert bleiben sichtbar.
- **Sprache:** Deutsch, neutrale Ansprache.

**Offene Punkte / Annahmen**

- `[ASSUMPTION]` **Scans:** Dateien vom Scanner oder Handy, Import per Drag-and-drop oder Dateiauswahl. Wenn direkt aus der App fotografiert werden soll, kommt eine Kamera-Route dazu. **Offen.**
- `[ASSUMPTION]` **Rangliste:** dieselbe App, optional im Vollbild auf Beamer oder TV.
- `[ASSUMPTION]` **Gesamtwertung:** Summe aller Durchgänge. Best-of-N oder Durchschnitt wären ein Umschalter in der Rangliste. **Offen.**
- `[ASSUMPTION]` **Gleichstand:** geteilter Rang als Default; eine Tie-Break-Regel kann ergänzt werden. **Offen.**
- `[ASSUMPTION]` **Schrägstrich:** 0 / kein Wurf. Wenn er auch „gestrichen“ bedeuten kann, braucht die Prüfung einen dritten Zustand. **Offen.**
- `[ASSUMPTION]` **Sternchen-Regel:** doppelte Sternwerte werden als Prüffall markiert, nicht automatisch verworfen. **Offen.**
- `[ASSUMPTION]` **Saubere Bögen:** „Bogen bestätigen“ ist eine bewusste Ein-Klick-Aktion; kein automatisches Bestätigen.
- `[ASSUMPTION]` **Namen:** optional; die Spieler-Nr. ist der Schlüssel.
- `[ASSUMPTION]` **Bogen:** bis zu 4 Spieler; ein Durchgang kann viele Bögen haben.
- `[ASSUMPTION]` **Excel:** ein Blatt pro Durchgang plus Gesamt; das genaue Template ist offen. **Offen.**
- `[ASSUMPTION]` **Runde abschließen:** sperrt die Runde; spätere Importe erzeugen eine neue Version. Aus dem Brainstorming, noch nicht bestätigt. **Offen.**
- `[ASSUMPTION]` **Out of scope:** Archiv, Spieler-Ansicht und Vorstands-/IT-Berichte aus dem Brainstorming sind nicht Teil der drei bestätigten Sichten. Sie können später als eigene Ansichten dazukommen. **Offen.**
