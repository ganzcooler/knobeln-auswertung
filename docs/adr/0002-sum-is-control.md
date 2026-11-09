# Summenzeile ist Kontrolle, keine Korrekturquelle

Status: accepted; manual fallback exception in [ADR-0004](0004-manual-results.md).

Die von den Spielern selbst gerechnete Summenzeile kann falsch sein. Die App berechnet die Summe immer aus den gelesenen Zellwerten, vergleicht sie mit der Bogensumme und markiert Abweichungen in der CSV; sie benutzt die Bogensumme nie, um Zellwerte zu erraten oder zu korrigieren. Zellwerte werden nur bei eindeutigen Handschrift-Artefakten (z. B. `8.5` → 85) oder einer gültigen, vom Rohwert abweichenden LLM-Lesung übernommen und dann markiert. Alternative wäre gewesen, die Zellen so lange anzupassen, bis die Bogensumme passt; das würde Lesefehler verschleiern und die menschliche Kontrolle unterlaufen.
