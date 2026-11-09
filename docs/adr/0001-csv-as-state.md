# CSV ist Ausgabe und Zustand

Status: superseded by [ADR-0003](0003-sqlite-as-state.md).

Die App muss neue Scans inkrementell in eine einzige, stabile `auswertung.csv` merged, die der Mensch in Excel als Datenquelle nutzt. Deshalb ist die CSV nicht nur Export, sondern auch der Zustand: Die App liest sie bei jedem Lauf, hängt neue Spieler/Durchgänge an, überschreibt bestehende Inhaltszeilen nie und meldet Datenkonflikte, statt sie automatisch aufzulösen. Alternative wäre ein voller Re-Export pro Lauf mit separater State-Datei gewesen; das hätte manuelle Korrekturen und den stabilen Excel-Bezug zerstört.
