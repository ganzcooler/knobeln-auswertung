# Knobeln-Auswertung

Kontext für die Auswertung gescannter Knobeln-Protokollbögen: handgeschriebene Punkte werden gelesen, gegen die selbst gerechnete Summe geprüft und als Excel-pivotfähige CSV ausgegeben.

## Language

**Bogen**:
Ein gescanntes Knobeln-Protokollblatt; eine Seite mit vier Spielerspalten, zwölf Wurf-Zeilen und einer Summenzeile.
_Avoid_: Blatt, Formular, Seite

**Durchgang**:
Die im Kopf des Bogens eingetragene Runde (1–5). Ein Durchgang kann mehrere Bögen mit je vier Spielern enthalten.
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
Der Ordner `input`, in den neue Scans gelegt werden. Er enthält nur noch nicht verarbeitete Bögen.
_Avoid_: Input, Queue, Warteschlange

**Duplikat**:
Zwei Lesungen desselben Spielers im selben Durchgang mit identischen Punkten. Ein Duplikat wird übersprungen.
_Avoid_: Konflikt, Doppelung

**Konflikt**:
Zwei Lesungen desselben Spielers im selben Durchgang mit unterschiedlichen Punkten. Ein Konflikt wird gemeldet, nicht automatisch überschrieben.
_Avoid_: Duplikat, Fehler

**Summenzeile**:
Die Zeile „Summe“ auf dem Bogen; enthält die von den Spielern selbst gerechnete Summe pro Spieler. Sie ist eine Kontrolle, keine Korrekturquelle.
_Avoid_: Gesamtsumme, Endsumme

**Auswertung**:
Die von der App aus den gelesenen Punkten berechnete Summe pro Spieler und Bogen.
_Avoid_: Ergebnis, Berechnung

**Warnung**:
Kennzeichnung einer Abweichung oder Unsicherheit in der CSV; führt nicht zu einer automatischen Korrektur der Summe.
_Avoid_: Fehler, Meldung

**Korrektur**:
Die domänenkonstante Ersetzung eines ungültigen Zellwerts durch einen Wert aus der Wertung, z. B. `8.5` → 85; wird immer als Warnung markiert. Ist der bereinigte Wert nicht in der Wertung, bleibt die Zelle leer.
_Avoid_: Auto-Korrektur, Fix
