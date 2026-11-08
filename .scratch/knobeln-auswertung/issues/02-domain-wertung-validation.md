# 02 — Domäne: Wertung, Normalisierung, Validierung

Status: resolved
Blocked by: 01

## Ziel

Die fachlichen Regeln als reine, testbare Python-Module: gültige Punktwerte, Zell-Normalisierung, Summenprüfung und Status-Codes.

## Aufgaben

- `domain/wertung.py`: vollständige Wertungstabelle und Menge der gültigen Punktwerte inkl. 0.
- `domain/models.py`: Datenmodelle für Bogen, Spieler, Wurf und Summenzeile.
- `domain/normalize.py`: `/` und `\` → 0, geschriebene 0 → 0, leere Zelle → `None`; Trennzeichen-Artefakte entfernen (`8.5` → 85, `10.5` → 105, `1.5` → 15, `8.0` → 80); keine Rundung, kein Klemmen.
- `domain/validation.py`: Bogen-, Zell-, Summen- und Identitätsprüfungen; Status-Codes und deutsche Warnungstexte.
- Die `*`-Markierung der Wertung wird ignoriert; keine Stern-Regel.
- Unit-Tests für Normalisierung, Summen (vollständig/unvollständig/fehlend/Delta), ungültige Werte und Status-Kombinationen.

## Abnahmekriterien

- `8.5` → 85, `10.5` → 105, `1.5` → 15, `8.0` → 80; `115`, `87`, `205` sind ungültig; `/` → 0; leer → fehlend.
- Die Summenzeile wird nie zur Zellkorrektur verwendet.
- Status-Codes entsprechen der Spec; mehrere Codes werden mit `|` verbunden.
- `uv run pytest` deckt die Domänenregeln ab.

## Referenzen

- `../spec.md` §3, §7
- `../../docs/adr/0002-sum-is-control.md`
