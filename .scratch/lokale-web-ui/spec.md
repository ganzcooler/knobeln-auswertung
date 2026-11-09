# Lokale Web-UI für die Knobeln-Auswertung

Status: ready-for-agent

## Problem Statement

Die heutige Anwendung ist eine CLI: Sie liest Scans per LLM, pflegt eine CSV und verschiebt auffällige Dateien in einen Review-Ordner. Am Veranstaltungstag braucht die Turnierleitung aber eine geführte lokale Oberfläche: Scans ablegen, den Stapel sehen, nur die auffälligen Fälle prüfen, Konflikte entscheiden, bei fehlender LLM-Verbindung Summen manuell erfassen und die Rangliste zeigen. Die CSV als Zustand und die verstreuten Ordner `input/` und `review/` passen nicht zu diesem Ablauf. Außerdem darf ein Netzausfall den Abend nicht blockieren, obwohl die Papierbögen vorhanden sind.

## Solution

Eine lokale Web-App auf `127.0.0.1` mit SQLite als Zustand und einem dauerhaften Scan-Archiv. Drei Sichten führen durch den Abend: **Scannen**, **Prüfen**, **Rangliste**. Die Prüfung folgt dem Prinzip **Review by Exception**: Nur Fälle, die die automatische Prüfung nicht bestehen, werden zu Prüffällen. Die Summenzeile bleibt bei gescannten Bögen eine Kontrolle, keine Korrekturquelle. Fehlt die LLM-Verbindung, kann die Turnierleitung pro Spieler und Durchgang eine Summe manuell erfassen; diese Durchgangsergebnisse sind sichtbar als „manuell“ markiert und zählen für die Rangliste. Die bestehende CLI bleibt als Batch-/Rettungsweg erhalten und arbeitet mit derselben Datenbank.

## User Stories

### Turnier und Durchgang

1. Als Turnierleitung möchte ich ein Turnier anlegen, damit ich alle Durchgänge eines Abends gemeinsam auswerten kann.
2. Als Turnierleitung möchte ich beim Start das zuletzt geöffnete Turnier wiedersehen, damit ich nach einer Pause sofort weiterarbeiten kann.
3. Als Turnierleitung möchte ich mehrere Turniere in derselben Datenbank verwalten, damit ich nicht mit mehreren Dateien hantieren muss.
4. Als Turnierleitung möchte ich ein Turnier umbenennen, damit die Rangliste den richtigen Namen trägt.
5. Als Turnierleitung möchte ich ein Turnier löschen können, damit Test- oder Fehlanlagen nicht dauerhaft bleiben.
6. Als Turnierleitung möchte ich vor dem Löschen eines Turniers eine Bestätigung sehen, damit nicht versehentlich Ergebnisse verschwinden.
7. Als Turnierleitung möchte ich die Durchgänge 1–5 eines Turniers anlegen und auswählen, damit ich den Abend in Runden strukturieren kann.
8. Als Turnierleitung möchte ich sehen, welcher Durchgang offen oder abgeschlossen ist, damit ich weiß, wo ich weiterarbeiten muss.
9. Als Turnierleitung möchte ich den Fortschritt „12 von 16 Bögen“ sehen, damit ich den Stapel überblicke.
10. Als Turnierleitung möchte ich einen Durchgang abschließen, damit die Rangliste final wird.
11. Als Turnierleitung möchte ich, dass „Durchgang abschließen“ bei offenen Prüffällen blockiert ist und den Grund nennt, damit keine vorläufigen Ergebnisse als final erscheinen.
12. Als Turnierleitung möchte ich einen abgeschlossenen Durchgang mit Bestätigung wieder öffnen, damit ich einen Fehler korrigieren kann.
13. Als Turnierleitung möchte ich, dass neue Scans für einen abgeschlossenen Durchgang abgelehnt werden, damit die finale Rangliste stabil bleibt.

### Scannen und Import

14. Als Turnierleitung möchte ich JPG-, PNG- und PDF-Dateien per Drag-and-drop ablegen, damit ich den Stapel schnell einlesen kann.
15. Als Turnierleitung möchte ich Dateien auch über einen Auswahl-Dialog hinzufügen, damit Drag-and-drop nicht der einzige Weg ist.
16. Als Turnierleitung möchte ich pro Datei einen Fortschritt sehen, damit ich weiß, was gerade passiert.
17. Als Turnierleitung möchte ich Fehler direkt an der Datei sehen, damit ich die richtige Datei erneut ablegen kann.
18. Als Turnierleitung möchte ich, dass eine fehlerhafte Datei sichtbar bleibt und nicht verloren geht, damit ich sie später erneut versuchen kann.
19. Als Turnierleitung möchte ich einen doppelten Scan erkennen, damit derselbe Bogen nicht zweimal in die Auswertung kommt.
20. Als Turnierleitung möchte ich bei einem Duplikat entscheiden, ob ich es behalte oder ignoriere, damit ich den Stapel kontrolliere.
21. Als Turnierleitung möchte ich, dass PDF-Seiten als einzelne Bögen behandelt werden, damit mehrseitige Scans vollständig ausgewertet werden.
22. Als Turnierleitung möchte ich die Original-Scans dauerhaft im Scan-Archiv wiederfinden, damit ich jede Zahl später am Bild erklären kann.
23. Als Turnierleitung möchte ich einen Scan erneut lesen lassen, damit ich nach einem Fehler keinen neuen Upload brauche.
24. Als Turnierleitung möchte ich Scans auch ohne Internetverbindung annehmen, damit der Stapel nicht blockiert.
25. Als Turnierleitung möchte ich wartende Scans sehen, damit ich weiß, welche Dateien auf die Extraktion warten.
26. Als Turnierleitung möchte ich, dass das Scan-Archiv lokal bleibt, damit keine Scans auf fremde Server gelangen.

### Extraktion

27. Als Turnierleitung möchte ich, dass die Extraktion im Hintergrund läuft, damit ich während des Einlesens weiterarbeiten kann.
28. Als Turnierleitung möchte ich den Browser schließen können, ohne dass laufende Extraktionen abbrechen, damit ich nicht am Rechner festklebe.
29. Als Turnierleitung möchte ich nach einem Server-Neustart den Zustand der Extraktionen wieder sehen, damit ich nicht raten muss, was fertig ist.
30. Als Turnierleitung möchte ich fehlgeschlagene Extraktionen erneut starten, damit ein temporärer Fehler nicht den Bogen blockiert.
31. Als Turnierleitung möchte ich Tokenverbrauch und geschätzte Kosten pro Extraktion sehen, damit ich die Kosten im Blick behalte.
32. Als Turnierleitung möchte ich ein Kostenlimit setzen, damit ein Lauf nicht unbemerkt teuer wird.
33. Als Turnierleitung möchte ich, dass die App ohne API-Key startet, damit Prüfen, manuelle Erfassung und Rangliste trotzdem funktionieren.
34. Als Turnierleitung möchte ich, dass die Extraktion bei fehlendem Key oder fehlendem Netz wartet und später erneut versucht wird, damit keine Datei verloren geht.

### Prüfen und Prüffälle

35. Als Turnierleitung möchte ich eine Queue der offenen Prüffälle sehen, damit ich nur die Fälle anschaue, die einen Menschen brauchen.
36. Als Turnierleitung möchte ich die Queue nach Schweregrad sortiert sehen: Summenfehler, unzulässiger Wert, unklare Ziffer, Konflikt, Kopfzeile, damit ich die wichtigsten Fälle zuerst erledige.
37. Als Turnierleitung möchte ich die Queue filtern können, damit ich mich auf eine Art von Problem konzentrieren kann.
38. Als Turnierleitung möchte ich, dass der erste offene Fall ausgewählt ist, damit ich ohne Suchen anfangen kann.
39. Als Turnierleitung möchte ich den betroffenen Bogen mit Bild und Werten sehen, damit ich die Entscheidung am Original treffen kann.
40. Als Turnierleitung möchte ich den Scan zoomen und verschieben, damit ich die Handschrift beurteilen kann.
41. Als Turnierleitung möchte ich die betroffene Zelle in der Wertetabelle markiert sehen, damit ich den Zusammenhang verstehe.
42. Als Turnierleitung möchte ich „Erkannt“, „Vorschlag“ und die zulässigen Werte sehen, damit ich eine fundierte Entscheidung treffe.
43. Als Turnierleitung möchte ich einen Vorschlag übernehmen, einen Wert korrigieren oder eine Zelle als unleserlich markieren, damit der Fall abgeschlossen wird.
44. Als Turnierleitung möchte ich den Summencheck mit berechneter und geschriebener Summe sehen, damit ich Abweichungen nachvollziehen kann.
45. Als Turnierleitung möchte ich Kandidatenzellen sehen, die eine Summenabweichung erklären könnten, damit ich nicht blind suche.
46. Als Turnierleitung möchte ich, dass die Summe nie automatisch einen Zellwert korrigiert, damit Lesefehler nicht geglättet werden.
47. Als Turnierleitung möchte ich einen Bogen mit einem Klick bestätigen, wenn es keine Auffälligkeiten gibt, damit saubere Bögen nicht durch Dialoge geschickt werden.
48. Als Turnierleitung möchte ich nach einer Entscheidung den nächsten Fall sehen, damit ich zügig weiterarbeiten kann.
49. Als Turnierleitung möchte ich ein „Gespeichert“ sehen und die letzte Korrektur rückgängig machen können, damit ein Fehlgriff nicht stehen bleibt.
50. Als Turnierleitung möchte ich den Rohwert auch nach einer Korrektur sehen, damit ich die Entscheidung erklären kann.
51. Als Turnierleitung möchte ich einen Konflikt zweier Erfassungen nebeneinander sehen, damit ich die richtige wählen kann.
52. Als Turnierleitung möchte ich bei einem Konflikt eine Erfassung wählen und die andere als „verworfen“ markieren, damit die Rangliste genau eine Erfassung verwendet.
53. Als Turnierleitung möchte ich, dass eine verworfene Erfassung nicht gelöscht wird, damit ich den Vorgang später erklären kann.
54. Als Turnierleitung möchte ich eine unklare Kopfzeile korrigieren, damit Spieler-Nr. und Durchgang eindeutig sind.
55. Als Turnierleitung möchte ich bei einem unleserlichen Bogen „Erneut lesen“ oder „Manuell erfassen“ wählen, damit der Abend weitergeht.
56. Als Turnierleitung möchte ich sehen, ob die Rangliste vorläufig oder bestätigt ist, damit ich den Status kenne.
57. Als Turnierleitung möchte ich bei „keine offenen Prüffälle“ direkt zur Rangliste oder zum Abschluss geführt werden, damit ich den nächsten Schritt nicht suche.

### Manuelle Durchgangsergebnisse

58. Als Turnierleitung möchte ich pro Spieler und Durchgang eine Summe manuell erfassen, damit ich bei fehlender LLM-Verbindung trotzdem eine Rangliste habe.
59. Als Turnierleitung möchte ich manuelle Ergebnisse als „manuell“ gekennzeichnet sehen, damit ich sie nicht mit gescannten Ergebnissen verwechsle.
60. Als Turnierleitung möchte ich manuelle Ergebnisse vor dem Abschluss bearbeiten, damit Tippfehler korrigiert werden können.
61. Als Turnierleitung möchte ich, dass ein später eintreffender Scan gegen ein manuelles Ergebnis einen Konflikt erzeugt, damit nichts still überschrieben wird.
62. Als Turnierleitung möchte ich, dass manuelle Ergebnisse für Rangliste und Abschluss zählen, damit der Abend ohne Extraktion abgeschlossen werden kann.
63. Als Turnierleitung möchte ich manuelle Ergebnisse auch offline erfassen, damit ein Netzausfall die Arbeit nicht stoppt.
64. Als Turnierleitung möchte ich, dass eine ungültige manuelle Summe abgelehnt wird, damit keine offensichtlich falschen Werte in die Rangliste kommen.
65. Als Turnierleitung möchte ich manuelle Ergebnisse im XLSX-Export als „manuell“ sehen, damit die Herkunft nachvollziehbar bleibt.

### Rangliste und Export

66. Als Turnierleitung möchte ich die Rangliste eines Durchgangs sehen, damit ich den Zwischenstand kenne.
67. Als Turnierleitung möchte ich eine Gesamtrangliste sehen, damit ich den Sieger des Turniers bestimme.
68. Als Turnierleitung möchte ich, dass die Gesamtwertung die Summe aller Durchgänge ist, damit die Wertung einfach und nachvollziehbar bleibt.
69. Als Turnierleitung möchte ich bei Gleichstand denselben Rang sehen, damit die Rangliste fair bleibt.
70. Als Turnierleitung möchte ich den Status „vorläufig“ oder „bestätigt“ über der Rangliste sehen, damit ich weiß, ob noch Prüffälle offen sind.
71. Als Turnierleitung möchte ich die Rangliste im Vollbild zeigen, damit sie auf dem Beamer lesbar ist.
72. Als Turnierleitung möchte ich leere Zustände mit dem nächsten Schritt sehen, damit ich nicht in einer Sackgasse lande.
73. Als Turnierleitung möchte ich die Quelle eines Ergebnisses sehen, damit ich gescannte und manuelle Ergebnisse unterscheiden kann.
74. Als Turnierleitung möchte ich die Rangliste als XLSX exportieren, damit ich sie archivieren oder in Excel weiterverwenden kann.
75. Als Turnierleitung möchte ich ein Blatt pro Durchgang plus ein Gesamtblatt im XLSX, damit die Datei verständlich bleibt.
76. Als Turnierleitung möchte ich bei einem Exportfehler eine klare Meldung und einen Retry sehen, damit die Rangliste nicht verschwindet.

### Offline, Hilfe und Bedienbarkeit

77. Als Turnierleitung möchte ich bei fehlender Verbindung einen ruhigen Hinweis sehen, damit ich weiß, dass nur die Extraktion betroffen ist.
78. Als Turnierleitung möchte ich die Verbindung erneut prüfen, damit ich sehe, ob der Dienst zurück ist.
79. Als Turnierleitung möchte ich eine kurze Hilfe mit den drei Schritten, Tastenkürzeln und Verbindungsstatus öffnen, damit ich nach einer Pause wieder hineinfinde.
80. Als Turnierleitung möchte ich die App mit der Tastatur bedienen können, damit ich schneller arbeiten kann.
81. Als Turnierleitung möchte ich, dass Status immer über Text und Farbe gezeigt wird, damit die Anzeige nicht nur farbabhängig ist.
82. Als Turnierleitung möchte ich, dass die App bei 200-%-Zoom und auf einem Tablet-Browserfenster benutzbar bleibt, damit ich flexibel arbeite.
83. Als Turnierleitung möchte ich deutsche Begriffe wie „Bogen“, „Durchgang“ und „Summe“ sehen, damit ich keine Entwicklerbegriffe lesen muss.
84. Als Turnierleitung möchte ich große, beschriftete Ziele, damit ich mit Maus und Touch nicht danebenklicke.
85. Als Turnierleitung möchte ich, dass `prefers-reduced-motion` respektiert wird, damit Bewegung nicht aufgezwungen wird.

### CLI und Betrieb

86. Als Entwicklerin möchte ich `knobeln` ohne Argument starten und die Web-UI öffnen, damit die primäre Bedienung offensichtlich ist.
87. Als Entwicklerin möchte ich `knobeln web` als expliziten Alias, damit ich den Server auch in Skripten klar starten kann.
88. Als Entwicklerin möchte ich `knobeln import [PFAD]` ausführen, damit ich große Stapel ohne Browser importieren kann.
89. Als Entwicklerin möchte ich `--db` und `--scans` angeben, damit ich mit einer anderen Datenbank oder einem anderen Archiv arbeiten kann.
90. Als Entwicklerin möchte ich, dass CLI und Web-UI dieselbe Datenbank verwenden, damit beide Wege denselben Zustand sehen.
91. Als Entwicklerin möchte ich, dass die alten CSV-Optionen entfallen, damit es keine zweite Wahrheit gibt.
92. Als Entwicklerin möchte ich, dass die App vor destruktiven Aktionen eine SQLite-Kopie anlegt, damit ein Fehlgriff nicht alle Daten kostet.
93. Als Entwicklerin möchte ich, dass die App nur auf `127.0.0.1` lauscht, damit die Daten nicht unbeabsichtigt im Netz landen.

## Implementation Decisions

### Architektur und Abhängigkeiten

- Python 3.13 mit FastAPI, Jinja2 und HTMX; HTMX wird lokal mitgeliefert, damit die UI ohne Internet funktioniert.
- Kein Node-Build und keine SPA. Die UI ist server-gerendert; HTMX übernimmt partielle Aktualisierungen.
- Ein gemeinsamer Anwendungskern (Use-Case-Service) wird von Web-UI und CLI genutzt. Die Web-Routen und die CLI enthalten keine Domänenlogik.
- Die bestehende Domänenlogik für Punkte, Summen, Status-Codes, Normalisierung und Merge bleibt die fachliche Grundlage; die CSV-Persistenz wird durch SQLite ersetzt.
- Der bestehende `LLMClient`-Vertrag bleibt der Seam zur Extraktion. Der OpenRouter-Client bleibt austauschbar und wird in Tests durch einen Fake ersetzt.

### Datenmodell und Zustand

- SQLite ist der Zustand. Es gibt keine CSV als Zustand und keinen CSV-Pflicht-Export.
- Alte `auswertung.csv`-Daten und der alte `review/`-Bestand werden ignoriert und nicht migriert.
- Eine Datenbank enthält mehrere Turniere. Das zuletzt geöffnete Turnier wird gemerkt.
- Ein Turnier enthält die Durchgänge 1–5, die Bögen und die Gesamtrangliste.
- Ein Bogen gehört zu genau einem Durchgang und enthält bis zu vier Spielerpositionen mit je zwölf Wurf-Zeilen und einer Summenzeile.
- Ein Spieler wird über die Spieler-Nr. innerhalb eines Turniers identifiziert; der Name ist optional.
- Ein Durchgangsergebnis ist die Summe eines Spielers in einem Durchgang. Es wird entweder aus einem gescannten Bogen berechnet oder manuell erfasst; die Herkunft bleibt sichtbar.
- Ein Prüffall ist eine abgeleitete Sicht auf die Status-Codes und LLM-Hinweise eines Bogens, keine eigene Wahrheit neben den Zellwerten.
- Ein Konflikt speichert beide Erfassungen. Eine wird als gültig gewählt, die andere als „verworfen“ markiert, aber nicht gelöscht.
- Die bestehenden Status-Codes bleiben die fachliche Grundlage; die UI übersetzt sie in deutsche Klartexte.
- `Geprueft` bleibt die Bestätigung für gescannte Gruppen. Manuelle Durchgangsergebnisse gelten durch die Eingabe als bestätigt und sind als „manuell“ markiert.

### Scan-Archiv und Import

- Original-Scans liegen dauerhaft in einem lokalen Scan-Archiv; die Datenbank referenziert die Dateien.
- Nach erfolgreicher Verarbeitung wird kein Scan gelöscht. Das frühere Aufräumen (saubere löschen, auffällige nach `review/`) entfällt.
- `input/` bleibt nur als Importordner für die CLI. Die Web-UI lädt direkt ins Scan-Archiv.
- Unterstützt werden JPG, PNG und PDF; PDF-Seiten werden als einzelne Bögen behandelt.
- Ein Duplikat wird über den Inhalts-Hash erkannt; die Turnierleitung entscheidet über Behalten oder Ignorieren.
- Nicht unterstützte Dateien werden gemeldet und bleiben sichtbar, ohne den Rest des Imports zu blockieren.

### Extraktion und Hintergrundverarbeitung

- Die Extraktion läuft als Hintergrundjob. Der Job-Zustand (`warten`, `läuft`, `fertig`, `Fehler`) liegt in SQLite.
- Die UI pollt per HTMX; ein laufender Job überlebt das Schließen des Browsers, solange der Server läuft.
- Nach einem Server-Neustart werden offene Jobs wieder aufgenommen.
- Standardmäßig wird sequenziell extrahiert, damit Kosten und Rate-Limits kontrollierbar bleiben.
- Standard-Reasoning für die Ziffernextraktion ist `medium`; `--reasoning` und `KNOBELN_REASONING` können es überschreiben.
- Tokenverbrauch und geschätzte Kosten werden pro Extraktion gespeichert und in der UI sichtbar gemacht.
- `--max-cost` bleibt als Kostenbremse erhalten; bei Überschreitung wird die weitere Extraktion gestoppt.
- Fehlt der API-Key oder das Netz, startet die Web-UI trotzdem. Uploads werden angenommen und warten; die Extraktion wird später erneut versucht.
- Der LLM-Cache bleibt erhalten und wird pro Bogen, Modell, Prompt-Version und Reasoning-Effort verwendet.

### Prüfen und Prüffälle

- Die Prüf-Queue wird aus den offenen Status-Codes und LLM-Hinweisen abgeleitet und nach Schweregrad sortiert: Summenfehler, unzulässiger Wert, unklare Ziffer, Konflikt, Kopfzeile, Bogen unklar.
- Die Queue ist filterbar; der erste offene Fall ist ausgewählt.
- Die Prüfansicht zeigt den ganzen Scan mit Zoom und Pan, dazu die Wertetabelle und den Summencheck. Ein automatischer Cell-Inspector mit deterministischer Rastererkennung ist nicht Teil von v1.
- Ein Prüffall zeigt auf Bogen, Spieler und gegebenenfalls Wurf-Nr.
- Aktionen: Vorschlag übernehmen, Wert korrigieren, Zelle als unleserlich markieren, Bogen bestätigen, Konflikt entscheiden, Kopfzeile korrigieren, Bogen erneut lesen.
- Entscheidungen werden sofort gespeichert. Ein Toast bestätigt „Gespeichert“ und bietet für die letzte Korrektur „Rückgängig“.
- Der Rohwert bleibt nach einer Korrektur sichtbar.
- „Bogen bestätigen“ setzt alle Gruppen des Bogens auf geprüft, wenn keine offenen Prüffälle mehr existieren. Saubere Bögen werden nicht automatisch bestätigt.
- „Durchgang abschließen“ ist blockiert, solange offene Prüffälle existieren; der Grund wird sichtbar genannt.
- Ein abgeschlossener Durchgang ist gesperrt. Neue Scans für diesen Durchgang werden abgelehnt; zum Korrigieren wird er mit Bestätigung wieder geöffnet. Eine Versionierung von Durchgängen gibt es in v1 nicht.
- Bei „Bogen unklar“ gibt es „Erneut lesen“ und „Manuell erfassen“.

### Manuelle Durchgangsergebnisse

- Manuelle Ergebnisse werden pro Spieler und Durchgang als eine Summe erfasst; zwölf Zellwerte sind nicht erforderlich.
- Die Eingabe erfolgt als einfache Tabelle mit „+ Spieler“; Spieler-Nr. ist Pflicht, Name optional.
- Die Summe wird gegen 0–2400 und die 5er-Regel geprüft. Ungültige Summen werden abgelehnt.
- Manuelle Ergebnisse sind sofort gültig, sichtbar als „manuell“ markiert und zählen für Rangliste und Abschluss.
- Manuelle Ergebnisse sind keine Prüffälle, solange die Summe gültig ist.
- Manuelle Ergebnisse werden nur für Spieler und Durchgänge angeboten, für die noch kein brauchbares gescanntes Ergebnis existiert.
- Trifft später ein Scan auf ein manuelles Ergebnis, entsteht ein Konflikt; der Mensch entscheidet, welche Erfassung gilt. Nichts wird still überschrieben.
- Vor dem Abschluss können manuelle Ergebnisse bearbeitet werden; nach dem Abschluss nur über das Wiederöffnen des Durchgangs.
- Manuelle Ergebnisse bleiben im XLSX-Export als „manuell“ erkennbar.

### Konflikte

- Zwei Erfassungen desselben Spielers im selben Durchgang mit unterschiedlichen Ergebnissen erzeugen einen Konflikt.
- Die Konflikt-Ansicht zeigt beide Erfassungen nebeneinander: Bogen, Werte, Summe und Status.
- Die Turnierleitung wählt eine Erfassung; die andere wird als „verworfen“ markiert, bleibt aber sichtbar und wird nicht gelöscht.
- Die Rangliste verwendet genau eine Erfassung.
- Ein Konflikt kann offen bleiben; der Durchgang kann dann nicht abgeschlossen werden.
- Ein späterer abweichender Scan öffnet einen bereits geprüften Konflikt wieder.

### Rangliste und Export

- Die Rangliste gibt es pro Durchgang und als Gesamtrangliste.
- Die Gesamtwertung ist die Summe aller Durchgangsergebnisse eines Spielers im Turnier.
- Gleichstand erzeugt denselben Rang mit dem Zusatz „geteilter Rang“; eine Tie-Break-Regel gibt es in v1 nicht.
- Die Rangliste zeigt den Status „vorläufig“ oder „bestätigt“ und verlinkt offene Prüffälle.
- Die Vollbild-Rangliste ist Teil von v1 und für den Beamer gedacht.
- Der XLSX-Export wird auf Knopfdruck erzeugt: ein Blatt pro Durchgang plus ein Gesamtblatt. Die Quelle „gescannt“/„manuell“ und der Status sind sichtbar.
- Ein Exportfehler lässt die Rangliste sichtbar und bietet einen Retry.

### CLI

- `knobeln` ohne Argument startet die Web-UI.
- `knobeln web` ist ein expliziter Alias für denselben Server.
- `knobeln import [PFAD]` importiert Scans aus einem Ordner ins Scan-Archiv und in die Datenbank.
- `--db` und `--scans` überschreiben die Standardpfade.
- `--model`, `--reasoning`, `--max-cost` und `--verbose` bleiben erhalten.
- Die alten CSV-Optionen (`--output`, `--review`, `--reset`, `--keep-input`) entfallen.
- CLI und Web-UI verwenden denselben Anwendungskern und dieselbe Datenbank.

### Web, Offline und Sicherheit

- Die Web-UI lauscht standardmäßig nur auf `127.0.0.1`. LAN-Zugriff gibt es in v1 nicht.
- Es gibt kein Login und keine Rollen; die App ist für ein bis zwei Personen am selben Laptop gedacht.
- Die App startet auch ohne API-Key und ohne Internet. Nur die Extraktion braucht den LLM-Dienst.
- Prüfen, manuelle Erfassung, Rangliste und XLSX-Export funktionieren vollständig lokal.
- Die Statusanzeige zeigt „Dienst erreichbar“, „Dienst nicht erreichbar“ oder „Status unbekannt“ mit „Erneut prüfen“.
- Die Gestaltung folgt den Tokens und Komponenten aus `DESIGN.md` (Papier und Tinte); `EXPERIENCE.md` liefert die Verhaltensregeln, soweit sie nicht durch diese Spec oder die ADRs ersetzt werden.
- Die UI ist deutsch, WCAG-2.2-AA-orientiert, mit sichtbarem Fokus, Text plus Farbe für Status und Zielen von mindestens 44 × 44 px.
- Die App respektiert `prefers-reduced-motion`; es gibt keinen Dark Mode und keine dekorativen Animationen.
- Vor destruktiven Aktionen (Turnier löschen, abgeschlossenen Durchgang wieder öffnen) legt die App eine SQLite-Kopie an.
- Die SQLite-Datei und das Scan-Archiv bleiben lokal und werden nicht in die Cloud synchronisiert.

## Testing Decisions

Ein guter Test prüft externes Verhalten an einem öffentlichen Seam, nicht Interna. Er bleibt gültig, wenn die Implementierung umgebaut wird. Erwartete Werte kommen aus einer unabhängigen Quelle: den Beispielen, den Golden-Daten oder einem von Hand gerechneten Fall.

### Bestätigte Seams

1. **Anwendungskern / Use-Case-Service (primärer Seam).**
   Alle fachlichen Abläufe werden über eine öffentliche Service-Schnittstelle getestet: Turnier und Durchgang anlegen, Scan importieren, Extraktionsjob verarbeiten, Prüffälle ableiten, Entscheidungen speichern, manuelles Ergebnis erfassen, Konflikt entscheiden, Durchgang abschließen/wieder öffnen, Rangliste berechnen, XLSX erzeugen. Tests nutzen eine temporäre SQLite-Datenbank und einen Fake-LLM. Das ist der höchste Seam, der Web-UI und CLI gemeinsam trägt.

2. **HTTP-/HTMX-Fläche (dünner sekundärer Seam).**
   Eine kleine Zahl von Tests über den FastAPI-Testclient prüft die Verdrahtung: Upload-Formular, manuelle Eingabe, eine Prüfentscheidung, Rangliste, Offline-Banner. Hier wird nicht die Fachlogik wiederholt, sondern Templates, Routen, Redirects und partielle Antworten.

3. **LLM-Client (bestehender Seam).**
   Die bestehenden Tests für Request-Form, Retry, Length-Retry, Reparatur-Retry und Cache bleiben erhalten. Der Fake-Client wird am Anwendungskern eingesetzt; der echte Modelltest bleibt manuell und kostenpflichtig.

Keine eigenen Seams für SQLite-Schema, Jinja-Interna oder HTMX-JavaScript. Diese werden über den Anwendungskern beziehungsweise die HTTP-Fläche abgedeckt.

### Testfälle am Anwendungskern

- Turnier und Durchgang anlegen, auswählen, abschließen, wieder öffnen.
- Import eines Beispiels, Duplikaterkennung, PDF-Mehrseiter.
- Extraktion mit Fake-LLM: sauberer Bogen, Summenabweichung, ungültiger Wert, unleserlicher Bogen.
- Prüffälle aus Status-Codes und LLM-Hinweisen ableiten; Sortierung und Filter.
- Entscheidung übernehmen/korrigieren/unleserlich; `Geprueft` und Neuberechnung.
- Konflikt zwischen zwei Erfassungen: beide bleiben erhalten, eine wird verworfen.
- Manuelles Ergebnis: gültig, ungültig, bearbeiten, Konflikt mit späterem Scan, Rangliste und Abschluss.
- Durchgang abschließen blockiert bei offenen Fällen; Wiederöffnen erlaubt Korrekturen.
- Gesamtrangliste: Summe, geteilter Rang, vorläufig/bestätigt.
- XLSX: Blätter pro Durchgang und Gesamt, Quelle und Status sichtbar.
- Offline: Job bleibt `warten`, App bleibt bedienbar, erneuter Versuch.
- Kostenlimit und Job-Fehler.

### Prior Art

- `tests/conftest.py`: Fake-LLM-Client und Beispieldaten.
- `tests/test_pipeline.py`: Ablauf import → Extraktion → Validierung → Persistenz → Aufräumen; wird für SQLite und Jobs adaptiert.
- `tests/test_merge.py`: Duplikat-, Konflikt- und `Geprueft`-Verhalten.
- `tests/test_models.py` und `tests/test_normalize.py`: Punkte, Summen, Status-Kombinationen.
- `tests/manual/`: echter Modell-Smoke-Test mit Golden-Daten; bleibt manuell und kostenpflichtig.

### Testgetriebene Umsetzung

Die Umsetzung erfolgt in vertikalen Scheiben mit `/tdd`: ein Test am vereinbarten Seam, dann die minimale Implementierung, dann der nächste Fall. Die volle Suite läuft am Ende jedes Tickets und vor dem Review.

## Out of Scope

- Cell-Inspector und deterministische Rastererkennung aus dem Scan.
- LAN-/Tablet-Zugriff von anderen Geräten; die App lauscht nur auf `127.0.0.1`.
- CSV als Zustand, CSV-Export und Migration alter CSV-Daten.
- Versionierung abgeschlossener Durchgänge bei Nachimport.
- Best-of-N, Durchschnitt oder Tie-Break-Regeln über den geteilten Rang hinaus.
- Kamera-Erfassung direkt aus der App.
- Druck/PDF und Prüfprotokoll.
- Login, Rollen, Audit-Trail, Mehrbenutzer-Synchronisation und Dark Mode.
- Andere Bogen-Layouts, Vereine oder Punktesysteme.
- Parallele Extraktion mehrerer Scans.
- Automatischer Excel-Refresh oder Power-Query-Vorlage.
- Spieler-Ansicht, Vorstandsberichte und Langzeit-Archiv außerhalb der lokalen Datenbank.
- Cloud-Backup oder Synchronisation.

## Further Notes

- `DESIGN.md` und `EXPERIENCE.md` sind Gestaltungsinput. Bei Widersprüchen gelten `GLOSSARY.md` und die ADRs; die entschiedenen Abweichungen sind dort festgehalten.
- `ADR-0003` ersetzt `ADR-0001`: SQLite ist der Zustand, CSV nicht mehr.
- `ADR-0004` ist die bewusste Ausnahme von `ADR-0002`: Manuelle Durchgangsergebnisse sind bei fehlender Extraktion eine zulässige Quelle, werden aber sichtbar als „manuell“ markiert.
- Die alte CLI-Spec und das alte README beschreiben den CSV-Stand. Diese Spec ersetzt den Web-UI-Teil; die alten Dokumente werden im Zuge der Umsetzung angepasst.
- Es wurde noch kein Prototyp gebaut. Die UI folgt den textlichen Spines; falls sich die Prüf-Werkbank im Build als unklar erweist, kann ein separater UI-Prototyp als Ticket nachgezogen werden.
- Die Test-Seams sind bestätigt: Anwendungskern als primärer Seam, HTTP-/HTMX-Fläche als dünner sekundärer Seam, bestehender LLM-Client-Seam.
- Implementiert wird erst nach ausdrücklicher Freigabe.
