# Knobeln-Auswertung

Kontext für die Auswertung gescannter Knobeln-Protokollbögen: handgeschriebene Punkte werden gelesen, gegen die selbst gerechnete Summe geprüft und als Excel-pivotfähige CSV ausgegeben.

## Language

**Bogen**:
Ein gescanntes Knobeln-Protokollblatt; eine Seite mit vier Spielerspalten, zwölf Wurf-Zeilen und einer Summenzeile.
_Avoid_: Blatt, Formular, Seite

**Turnier**:
Die Veranstaltung, für die Bögen erfasst und ausgewertet werden; enthält die Durchgänge 1–5 und die Gesamtrangliste.
_Avoid_: Veranstaltung, Wettbewerb

**Durchgang**:
Ein Abschnitt eines Turniers mit der Nummer 1–5 im Bogenkopf; ein Durchgang kann mehrere Bögen mit je vier Spielern enthalten.
_Avoid_: Runde, Spielrunde

**Spieler**:
Ein Teilnehmer am Knobeln, identifiziert durch die Spieler-Nr.; der Name ist optional.
_Avoid_: Teilnehmer, Person

**Spieler-Nr.**:
Die handgeschriebene Nummer eines Spielers; eindeutig für die Veranstaltung und über die Durchgänge stabil.
_Avoid_: Startnummer, ID

**Wurf-Nr.**:
Die Zeile 1–12 auf dem Bogen. Nicht zu verwechseln mit dem „Wurf“ der Wertungstabelle.
_Avoid_: Runde, Versuch

**Wurf**:
Die Würfelkombination, der die gedruckte Wertungstabelle Punkte zuordnet (z. B. 104, 222*). Die App liest sie nicht.
_Avoid_: Wurf-Nr.

**Punkte**:
Der pro Wurf-Zelle eingetragene Punktwert; entweder 0 (Schrägstrich) oder ein Wert aus der Wertungstabelle.
_Avoid_: Ergebnis, Score

**Wertung**:
Die gedruckte Tabelle, die Würfen Punktwerte zuordnet und damit die gültigen Punktwerte definiert. Sie ist für das gesamte Spiel konstant und auf jedem Bogen gleich.
_Avoid_: Punktetabelle, Skala

**Eingang**:
Der Ordner `input`, aus dem die CLI neue Scans in das Scan-Archiv importiert; er enthält nur noch nicht importierte Bögen.
_Avoid_: Input, Queue, Warteschlange

**Scan-Archiv**:
Der dauerhafte lokale Ordner mit den Original-Scans; die Datenbank referenziert die Dateien.
_Avoid_: Review-Ordner, Upload-Ordner

**Duplikat**:
Zwei Lesungen desselben Spielers im selben Durchgang mit identischen Punkten. Ein Duplikat wird übersprungen.
_Avoid_: Konflikt, Doppelung

**Konflikt**:
Zwei Erfassungen desselben Spielers im selben Durchgang mit unterschiedlichen Ergebnissen; beide bleiben erhalten, der Mensch entscheidet, welche gilt.
_Avoid_: Duplikat, Fehler

**Summenzeile**:
Die Zeile „Summe“ auf dem Bogen; enthält die von den Spielern selbst gerechnete Summe pro Spieler. Sie ist eine Kontrolle, keine Korrekturquelle.
_Avoid_: Gesamtsumme, Endsumme

**Auswertung**:
Die von der App aus den gelesenen Punkten berechnete Summe pro Spieler und Bogen.
_Avoid_: Ergebnis, Berechnung

**Durchgangsergebnis**:
Die Summe eines Spielers in einem Durchgang; sie wird aus einem gescannten Bogen berechnet oder bei fehlender Extraktion manuell erfasst und bleibt als solche gekennzeichnet.
_Avoid_: Summe, Endsumme

**Warnung**:
Kennzeichnung einer Abweichung oder Unsicherheit in der Auswertung; führt nicht zu einer automatischen Korrektur der Summe.
_Avoid_: Fehler, Meldung

**Prüffall**:
Ein aus den Status-Codes abgeleiteter offener Punkt eines Bogens, den ein Mensch entscheiden muss; keine eigene Wahrheit neben den Zellwerten.
_Avoid_: Fehler, Issue

**Korrektur**:
Die domänenkonstante Ersetzung eines ungültigen Zellwerts durch einen Wert aus der Wertung, z. B. `8.5` → 85; wird immer als Warnung markiert. Ist der bereinigte Wert nicht in der Wertung, bleibt die Zelle leer.
_Avoid_: Auto-Korrektur, Fix
