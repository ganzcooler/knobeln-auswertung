# SQLite ist der Zustand

Status: accepted.

Die Anwendung führt ihren Zustand in einer lokalen SQLite-Datenbank; die CLI arbeitet mit derselben Datenbank. Die bisherige `auswertung.csv` ist nicht mehr Zustand und nicht mehr Pflichtausgabe, weil Review-Entscheidungen, Konfliktalternativen und Scan-Metadaten transaktional gehalten werden müssen und sich in einer pivotfähigen CSV nicht sauber abbilden lassen. Excel bleibt ein möglicher Export-Empfänger, nicht die Datenquelle. Alternative wäre CSV als Zustand plus ableitbarer SQLite-Index gewesen; das hätte zwei Wahrheiten und Synchronisation erzeugt. ADR-0001 ist damit ersetzt; eine Migration bestehender CSV-Daten ist nicht Teil dieser Entscheidung.
