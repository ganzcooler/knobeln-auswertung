---
name: Knobeln-Auswertung
description: Lokale Werkbank für das Digitalisieren, Prüfen und Auswerten handgeschriebener Knobeln-Spielprotokolle.
status: final
updated: 2026-11-09
colors:
  paper: '#F5EFE2'
  paper-raised: '#FFFCF5'
  paper-deep: '#E8DDC8'
  ink: '#1E2A33'
  ink-soft: '#5B6469'
  ink-faint: '#8A8F91'
  blue: '#245A8D'
  blue-strong: '#173F66'
  blue-wash: '#DCE8F2'
  red: '#A33B32'
  red-wash: '#F4DED9'
  green: '#3F6B4F'
  green-wash: '#DDE9DF'
  amber: '#8A5F1F'
  amber-wash: '#F3E6CC'
  border: '#D6CBB8'
  border-strong: '#8F846F'
  focus: '#245A8D'
typography:
  display:
    fontFamily: 'Inter, Segoe UI, system-ui, -apple-system, sans-serif'
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  heading:
    fontFamily: 'Inter, Segoe UI, system-ui, -apple-system, sans-serif'
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  body:
    fontFamily: 'Inter, Segoe UI, system-ui, -apple-system, sans-serif'
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0
  label:
    fontFamily: 'Inter, Segoe UI, system-ui, -apple-system, sans-serif'
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.08em
  number:
    fontFamily: 'Cascadia Code, Consolas, monospace'
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: 0.01em
  number-lg:
    fontFamily: 'Cascadia Code, Consolas, monospace'
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.01em
  number-xl:
    fontFamily: 'Cascadia Code, Consolas, monospace'
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.01em
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  '7': 48px
  '8': 64px
components:
  top-bar:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    height: 64px
  tab-active:
    foreground: '{colors.ink}'
    accent: '{colors.blue}'
  tab-inactive:
    foreground: '{colors.ink-soft}'
  round-header:
    foreground: '{colors.ink}'
    background: 'transparent'
    borderColor: '{colors.border}'
  drop-zone:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border-strong}'
    radius: '{rounded.md}'
    padding: '{spacing.7}'
  sheet-card:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  review-queue:
    background: '{colors.paper}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  review-queue-item:
    background: '{colors.paper-raised}'
    borderColor: '{colors.red}'
    radius: '{rounded.sm}'
  review-queue-item-selected:
    background: '{colors.blue-wash}'
    borderColor: '{colors.blue}'
  cell-inspector:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  sum-check:
    background: '{colors.paper-deep}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  sheet-review:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  conflict-view:
    background: '{colors.paper}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  leaderboard-table:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    headerBackground: '{colors.paper-deep}'
    radius: '{rounded.md}'
  status-badge:
    fontFamily: '{typography.label.fontFamily}'
    fontSize: '{typography.label.fontSize}'
    fontWeight: '{typography.label.fontWeight}'
    radius: '{rounded.full}'
  status-confirmed:
    background: '{colors.green-wash}'
    foreground: '{colors.green}'
    radius: '{rounded.full}'
  status-provisional:
    background: '{colors.amber-wash}'
    foreground: '{colors.amber}'
    radius: '{rounded.full}'
  status-open:
    background: '{colors.red-wash}'
    foreground: '{colors.red}'
    radius: '{rounded.full}'
  primary-button:
    background: '{colors.blue}'
    foreground: '{colors.paper-raised}'
    radius: '{rounded.md}'
  secondary-button:
    background: 'transparent'
    foreground: '{colors.ink}'
    borderColor: '{colors.border-strong}'
    radius: '{rounded.md}'
  number-cell:
    fontFamily: '{typography.number.fontFamily}'
    fontSize: '{typography.number.fontSize}'
    textAlign: 'right'
  help-dialog:
    background: '{colors.paper-raised}'
    borderColor: '{colors.border}'
    radius: '{rounded.lg}'
  toast:
    background: '{colors.ink}'
    foreground: '{colors.paper-raised}'
    radius: '{rounded.md}'
  status-banner:
    background: '{colors.paper-deep}'
    borderColor: '{colors.border}'
    radius: '{rounded.md}'
  empty-state:
    background: '{colors.paper}'
    foreground: '{colors.ink}'
    radius: '{rounded.md}'
---

## Brand & Style

Die Knobeln-Auswertung ist eine **Werkbank**, kein Enterprise-Dashboard. Auf dem Tisch liegt ein Stapel handgeschriebener Bögen; daneben ein Laptop, auf dem dieselben Bögen geprüft und zu einer Rangliste werden. Die visuelle Sprache nimmt diese Situation auf: warmes Papier, dunkle Tinte, ein blauer Handschrift-Akzent, rote Prüfmarken und grüne Bestätigungsstempel. Die Anwendung darf nach Papier aussehen, aber sie darf nicht so tun, als wäre sie Papier: Zahlen und Status stehen immer in einer klaren, gut lesbaren UI-Schrift, nie in einer Handschrift.

Die drei Sichten – **Scannen**, **Prüfen**, **Rangliste** – sind Stationen auf demselben Tisch. Die Oberfläche soll sich wie ein geführter Ablauf anfühlen: Der nächste Schritt ist immer sichtbar, und die Anwendung erklärt in einfacher Sprache, was gerade passiert. Die Turnierleitung besteht aus ein bis zwei computer-affinen Personen, nicht aus Entwicklern; die UI verwendet keine Fachbegriffe aus OCR, LLM oder Datenbanken.

Die visuelle Richtung „Papier und Tinte“ ist bestätigt. Sie ist kein Dogma; wenn später eine andere Richtung gewünscht ist, werden die Tokens ersetzt, ohne die Informationsarchitektur zu ändern.

## Colors

Die Palette ist bewusst klein. Farbe trägt Bedeutung, nicht Dekoration.

- **Papier (`{colors.paper}`)** ist der ruhige Hintergrund der gesamten Anwendung. `{colors.paper-raised}` liegt auf Karten, Tabellen und Eingaben; `{colors.paper-deep}` markiert zusammengehörige Blöcke wie den Summencheck.
- **Tinte (`{colors.ink}`)** ist die primäre Textfarbe. `{colors.ink-soft}` für sekundäre Texte; `{colors.ink-faint}` nur für deaktivierte Zustände und dekorative Details. Platzhaltertexte nutzen `{colors.ink-soft}`.
- **Handschrift-Blau (`{colors.blue}`)** ist die primäre Aktionsfarbe: Buttons, aktive Tabs, Fokus, ausgewählte Prüffälle. `{colors.blue-strong}` für Hover und gedrückte Zustände, `{colors.blue-wash}` für ausgewählte Zeilen und ruhige Hervorhebungen.
- **Prüf-Rot (`{colors.red}`)** bedeutet „hier muss ein Mensch entscheiden“: offene Prüffälle, Summenabweichungen, unzulässige Werte, Konflikte. `{colors.red-wash}` ist der Hintergrund für offene Status-Badges.
- **Bestätigt-Grün (`{colors.green}`)** bedeutet „geprüft und freigegeben“. `{colors.green-wash}` ist der Hintergrund für bestätigte Status-Badges. Grün wird nie für primäre Aktionen verwendet.
- **Vorläufig-Amber (`{colors.amber}`)** bedeutet „die Rangliste ist noch nicht final“. `{colors.amber-wash}` ist der Hintergrund für vorläufige Status-Badges.
- **Linien:** `{colors.border}` ist eine Haarlinie für Struktur; `{colors.border-strong}` markiert interaktive Grenzen wie Eingaben, sekundäre Buttons und die Drop-Zone.

Farbe ist nie das einzige Signal: Jeder Status trägt zusätzlich Text („Offen“, „Vorläufig“, „Bestätigt“). Rot und Grün werden nie als reine Flächen hinter kritischen Zahlen verwendet; die Zahl bleibt in `{colors.ink}`.

Kontrastziele für die tragenden Kombinationen: `{colors.ink}` auf `{colors.paper}` mindestens 7:1; `{colors.ink-soft}` auf `{colors.paper}` mindestens 4,5:1; `{colors.paper-raised}` auf `{colors.blue}` mindestens 4,5:1; `{colors.red}`, `{colors.green}` und `{colors.amber}` auf ihren jeweiligen Washes mindestens 4,5:1. `{colors.border}` ist keine interaktive Grenze; dafür `{colors.border-strong}`.

## Typography

Drei Rollen, klar getrennt:

- **Display und Überschriften** in einer modernen Sans-Serif (`{typography.display.fontFamily}`, `{typography.heading.fontFamily}`). Sie geben der Werkbank einen klaren, zeitgemäßen Ton und tragen die Namen der drei Sichten. Display: `{typography.display.fontSize}`, Überschrift: `{typography.heading.fontSize}`.
- **UI und Fließtext** in derselben Sans-Serif (`{typography.body.fontFamily}`, `{typography.label.fontFamily}`). Buttons, Tabellen, Formulare und Hilfetexte bleiben nüchtern und gut lesbar. Grundgröße: `{typography.body.fontSize}`.
- **Zahlen** in einer Monospace-Schrift mit Tabellenziffern (`{typography.number.fontFamily}`, `{typography.number-lg.fontFamily}`, `{typography.number-xl.fontFamily}`). Jede Punktzahl, jede Summe und jede Spieler-Nr. steht in dieser Schrift. Das ist die wichtigste typografische Regel: Zahlen sind Daten, keine Dekoration.
- **Scan-Vorschau:** Die Handschrift in der Scan-Vorschau ist die Abbildung des Originalbogens, nicht die UI-Typografie. Die Anwendung selbst bleibt durchgehend bei der Sans-Serif für Text und der Monospace für Zahlen.

Prüfwerte und Summen stehen mindestens in `{typography.number.fontSize}`, die große Summe im Summencheck in `{typography.number-lg.fontSize}`. Die Rangliste im Vollbild skaliert auf mindestens `{typography.heading.fontSize}` für Namen und `{typography.number-xl.fontSize}` für Summen. Labels sind in `{typography.label.fontSize}` gesetzt und tragen `{typography.label.letterSpacing}`.

## Layout & Spacing

Der Abstandsraster ist 8 px (`{spacing.1}` bis `{spacing.8}`). Die Anwendung nutzt eine maximale Inhaltsbreite von 1280 px; die Prüf-Ansicht darf die volle Breite nutzen, weil Bild und Tabelle nebeneinander Platz brauchen.

- **Scannen:** zentrierte Einwurfzone, darunter der Stapel. Die Seite bleibt großzügig und ruhig; der wichtigste Inhalt ist die Drop-Zone.
- **Prüfen:** zweigeteilte Werkbank. Links die Review-Queue (ca. 360–420 px), rechts der Bogen mit Bild und Cell-Inspector. Auf schmalen Bildschirmen stapeln sich Queue und Detail; die Queue wird dann zu einer horizontalen Liste.
- **Rangliste:** breite Tabelle mit klebender Kopfzeile. Auf großen Bildschirmen bleibt die Tabelle zentriert; im Vollbild nutzt sie die gesamte Fläche.

Die drei Sichten teilen sich eine feste Top-Bar mit Durchgangsauswahl, Tabs und Status. Die Top-Bar ist maximal 64 px hoch und bleibt beim Scrollen sichtbar.

## Elevation & Depth

Tiefe entsteht durch Ton und feine Linien, nicht durch schwere Schatten. Karten und Tabellen liegen auf `{colors.paper-raised}` und werden mit `{colors.border}` abgegrenzt. Der Scan selbst ist die visuelle Hauptfläche; er bekommt einen sehr weichen, warmen Schatten, damit er wie ein Blatt auf dem Tisch wirkt. Dialoge und die Vollbild-Rangliste dürfen einen stärkeren, aber weichen Schatten tragen. Keine gestapelten Karten, keine schwebenden Panels, keine Glas-Effekte.

## Shapes

Kleine Radien: `{rounded.sm}` für Eingaben und Zellen, `{rounded.md}` für Karten, Buttons und Drop-Zone, `{rounded.lg}` für Dialoge. Status-Badges sind die einzige Ausnahme und dürfen `{rounded.full}` nutzen. Die Formsprache ist „Werkzeug“, nicht „Consumer-App“: keine Pill-Buttons, keine verspielten Blobs.

## Components

- **Top-Bar** – `{components.top-bar}`. Höhe `{components.top-bar.height}`, Hintergrund `{components.top-bar.background}`, untere Haarlinie `{components.top-bar.borderColor}`. Links der Produktname, daneben die Durchgangsauswahl. Rechts die drei Tabs mit Zahlen und ein Hilfe-Link. Bleibt beim Scrollen sichtbar.
- **Tab** – aktiv: `{components.tab-active}` mit blauer Unterkante; inaktiv: `{components.tab-inactive}`. Die Zahl am Tab ist immer eine Zahl plus Text, nie nur ein Punkt. Aktiver Tab in `{colors.ink}`, inaktiver Tab in `{colors.ink-soft}`.
- **Round-Header** – `{components.round-header}`. Kompakter Block in der Top-Bar: Durchgangsauswahl, Fortschritt („12 von 16 Bögen“) in `{typography.label.fontSize}` und die Aktion „Runde abschließen“. Deaktiviert: Text in `{colors.ink-faint}`, Grund sichtbar daneben.
- **Drop-Zone** – `{components.drop-zone}`. Große gestrichelte Fläche, `{components.drop-zone.borderColor}`, Radius `{components.drop-zone.radius}`, Innenabstand `{components.drop-zone.padding}`. Beschriftung „Bögen hier ablegen“ in `{typography.heading.fontSize}`, sekundärer Button „Dateien auswählen“. Drag-over: `{colors.blue-wash}`-Fläche und `{colors.blue}`-Rahmen. Fortschritt pro Datei als schmale Leiste.
- **Sheet-Card** – `{components.sheet-card}`. Vorschaubild, Dateiname in `{typography.body.fontSize}`, Durchgang und Spielerzahl in `{typography.label.fontSize}`, Status-Badge rechts. Hintergrund `{components.sheet-card.background}`, Rahmen `{components.sheet-card.borderColor}`, Radius `{components.sheet-card.radius}`. Fehlerzustand: roter linker Rand und Inline-Text.
- **Review-Queue** – `{components.review-queue}`. Eigene Spalte (360–420 px) mit eigenem Scrollbereich; darüber die Filterleiste. Ausgewählter Eintrag: `{components.review-queue-item-selected}`. Leerer Zustand zentriert in der Spalte. Auf schmalen Bildschirmen horizontale Liste.
- **Review-Queue-Item** – `{components.review-queue-item}`. Linker Schweregrad-Rand: Summenfehler und unzulässiger Wert `{colors.red}`, unklare Ziffer `{colors.amber}`, Konflikt `{colors.blue}`, Kopfzeile `{colors.ink-soft}`. Oben Spieler und Wurf in `{typography.label.fontSize}`, darunter Rohwert und Vorschlag in `{typography.number.fontSize}`, rechts Status-Badge. Ausgewählt: `{components.review-queue-item-selected}`.
- **Cell-Inspector** – `{components.cell-inspector}`. Großer Bildausschnitt der Zelle **aus dem Original-Scan** auf `{components.cell-inspector.background}`, Rahmen `{components.cell-inspector.borderColor}`, Radius `{components.cell-inspector.radius}`. Die Zellkoordinaten kommen aus der deterministischen Rastererkennung, nicht aus dem LLM. Darunter „Erkannt“, „Vorschlag“ und die zulässigen Werte in `{typography.number.fontSize}`. Drei Aktionen als Primary Button und Secondary Buttons, immer sichtbar. Bild fehlt: Dateiname und „Erneut lesen“.
- **Sum-Check** – `{components.sum-check}`. Block in `{components.sum-check.background}`, Radius `{components.sum-check.radius}`, Rahmen `{components.sum-check.borderColor}`. „Berechnet“ und „Geschrieben“ in `{typography.number-lg.fontSize}`, darunter die Differenz in `{colors.red}` (bei 0 in `{colors.green}`) und ein Satz, welche Zellen den Unterschied erklären könnten. Kandidatenzellen in `{typography.number.fontSize}`. Die Zahlen bleiben in `{colors.ink}`; Rot/Grün sind Text- und Markierungsfarben, keine Füllflächen hinter den Zahlen.
- **Sheet-Review** – `{components.sheet-review}`. Tabelle 4 Spieler × 12 Würfe auf `{components.sheet-review.background}`, Rahmen `{components.sheet-review.borderColor}`, Radius `{components.sheet-review.radius}`. Kopfzeile in `{typography.label.fontSize}`, Zellen in `{typography.number.fontSize}`. Korrigierte Werte in `{colors.blue}`, Rohwert klein in `{colors.ink-soft}` daneben; offene Zellen mit `{colors.red}`-Marker.
- **Conflict-View** – `{components.conflict-view}`. Zwei gleich breite Spalten auf `{components.conflict-view.background}`; jede Seite eine Sheet-Card mit Bild, Werten, Summe und Status. Ungeklärt: beide Seiten mit `{colors.red}`-Rahmen. Gewählt: `{colors.green}`-Rahmen und `{colors.green-wash}`-Kopf; verworfen: `{colors.ink-faint}` und Label „verworfen“, aber sichtbar. Kein Modal.
- **Leaderboard Table** – `{components.leaderboard-table}`. Breite Tabelle auf `{components.leaderboard-table.background}`, Kopfzeile `{components.leaderboard-table.headerBackground}` und klebend, Rahmen `{components.leaderboard-table.borderColor}`, Radius `{components.leaderboard-table.radius}`. Rang und Spieler-Nr. in `{typography.number.fontSize}`, Name in `{typography.body.fontSize}`, Durchgänge in `{typography.number.fontSize}`, Summe in `{typography.number-lg.fontSize}`, Status-Badge. Vollbild: Name in `{typography.heading.fontSize}`, Summe in `{typography.number-xl.fontSize}`. Gleichstand: gleiche Rangzahl, Zusatz „geteilter Rang“ in `{typography.label.fontSize}`.
- **Status-Badge** – `{components.status-badge}`. Text in `{typography.label.fontFamily}`, `{typography.label.fontSize}`, `{typography.label.fontWeight}`; Radius `{components.status-badge.radius}`. Varianten: `{components.status-confirmed}`, `{components.status-provisional}`, `{components.status-open}`. Immer Text plus Farbe.
- **Primary Button** – `{components.primary-button}`. Blau gefüllt, Text in `{colors.paper-raised}`, Radius `{components.primary-button.radius}`. Genau eine primäre Aktion pro Zustand. Hover `{colors.blue-strong}`, Fokusring `{colors.focus}`. Deaktiviert: `{colors.ink-faint}`, kein Blau.
- **Secondary Button** – `{components.secondary-button}`. Transparent, Text in `{colors.ink}`, Rahmen `{components.secondary-button.borderColor}`, Radius `{components.secondary-button.radius}`. Für „Abbrechen“, „Später“, „Exportieren“, „Vollbild“. Hover: `{colors.blue-wash}`.
- **Number Cell** – `{components.number-cell}`. Rechtsbündig, tabellarisch, `{components.number-cell.fontFamily}` und `{components.number-cell.fontSize}`. Rohwert und korrigierter Wert bleiben unterscheidbar. Nie in Handschrift.
- **Help-Dialog** – `{components.help-dialog}`. Dialog auf `{components.help-dialog.background}`, Rahmen `{components.help-dialog.borderColor}`, Radius `{components.help-dialog.radius}`. Drei nummerierte Schritte, Tastenkürzel-Tabelle, Verbindungsstatus. Maximal eine Dialogebene.
- **Toast** – `{components.toast}`. Kurzer Hinweis auf `{components.toast.background}` mit Text in `{components.toast.foreground}`, Radius `{components.toast.radius}`. Unten mittig; verdeckt nie die aktive Zelle oder die primäre Aktion. Nur ein Toast gleichzeitig.
- **Status-Banner** – `{components.status-banner}`. Volle Breite über Tabelle oder Queue, `{components.status-banner.background}`, Rahmen `{components.status-banner.borderColor}`, Radius `{components.status-banner.radius}`. Varianten: vorläufig `{colors.amber-wash}`/`{colors.amber}`, bestätigt `{colors.green-wash}`/`{colors.green}`, offline `{colors.red-wash}`/`{colors.red}`. Text plus Aktion; verdeckt nie den Inhalt.
- **Empty State** – `{components.empty-state}`. Zentrierter Block auf `{components.empty-state.background}`, Text in `{components.empty-state.foreground}`, Radius `{components.empty-state.radius}`. Überschrift in `{typography.heading.fontSize}`, ein Satz in `{typography.body.fontSize}`, genau eine primäre Aktion.

Visuelle Referenzen: [Scannen](mockups/scannen.html) · [Prüfen](mockups/pruefen.html) · [Rangliste](mockups/rangliste.html) · [Konflikt](mockups/konflikt.html). Die Mockups sind illustrativ; bei Widersprüchen gewinnen die Spines.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Den Original-Scan immer neben dem Wert zeigen | Den Scan hinter einem Modal verstecken |
| Rohwert und korrigierten Wert unterscheidbar halten | Den Rohwert nach einer Korrektur überschreiben |
| Die Summe als Kontrolle zeigen, nie als Quelle | Einen Einzelwert automatisch an die Summe anpassen |
| Konflikte nebeneinander zeigen | Eine Erfassung stillschweigend überschreiben |
| Text und Farbe für Status kombinieren | Status nur über Farbe codieren |
| Vorläufig und bestätigt sichtbar trennen | Eine vorläufige Zahl als Tatsache darstellen |
| Den nächsten Schritt immer sichtbar machen | Die Turnierleitung suchen lassen, wo es weitergeht |
| Den häufigen Fall „keine Auffälligkeiten“ in einem Klick bestätigen | Auch saubere Bögen durch zehn Dialoge schicken |
| Zahlen in `{typography.number.fontFamily}` setzen | Werte in einer Handschrift-Schrift anzeigen |
| Große, gut lesbare Ziele für Maus und Touch | Icon-only-Buttons ohne Label |
| Ruhige, papierähnliche Flächen | Dunkelmodus, Verläufe, Animationen als Selbstzweck |
| Klare deutsche Begriffe („Bogen“, „Durchgang“, „Summe“) | „OCR“, „LLM“, „Validierung“, „Entity“ in der UI |
