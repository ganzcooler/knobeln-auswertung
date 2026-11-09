# Manuelle Durchgangsergebnisse bei fehlender Extraktion

Status: accepted.

Wenn am Veranstaltungstag die Verbindung zum LLM-Dienst fehlt, muss die Turnierleitung pro Spieler und Durchgang eine Summe manuell erfassen können. Diese manuelle Summe wird als Durchgangsergebnis gespeichert, sichtbar als „manuell“ markiert und von der Rangliste verwendet. Sie ist eine bewusste Ausnahme von ADR-0002, weil ohne Scan keine Zellwerte zur Kontrolle existieren. Für gescannte Bögen bleibt ADR-0002 unverändert.

Manuelle Ergebnisse sind nur für Spieler und Durchgänge vorgesehen, für die noch kein brauchbares gescanntes Ergebnis existiert. Trifft später ein Scan auf ein manuelles Ergebnis, entsteht ein Konflikt, den der Mensch entscheidet; nichts wird still überschrieben. Die Summe wird gegen 0–2400 und die 5er-Regel geprüft. Alternative wäre gewesen, den Abend ohne Auswertung zu beenden oder die Papierbögen nachträglich zu scannen; beides verfehlt den Zweck der Werkbank.
