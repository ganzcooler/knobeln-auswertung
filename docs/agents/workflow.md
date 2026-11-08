# Feature Workflow

Feature-Arbeit folgt der Skill-Pipeline in `.agents/skills/ask-matt`:

1. **`/grill-with-docs`** — Idee schärfen, `GLOSSARY.md` und ADRs pflegen.
2. **Freigabe-Gate.** Nach dem Grilling nicht implementieren, bis der Nutzer ausdrücklich zustimmt. Das Grilling endet mit gemeinsamem Verständnis, nicht mit Code.
3. **`/to-spec`** — bei Multi-Session-Arbeit die Spec aus dem Gespräch ableiten; Test-Seams mit dem Nutzer bestätigen.
4. **`/to-tickets`** — vertikale Tracer-Bullets mit Blocking-Edges; die Zerlegung mit dem Nutzer abstimmen.
5. **`/implement`** pro Ticket, mit **`/tdd`** an den vereinbarten Seams. Zwischendurch Typprüfung und einzelne Tests, am Ende die volle Suite.
6. **`/code-review`** — Standards- und Spec-Achse getrennt, mit frischen Kontextfenstern.
7. **`/pr`** beim Hochgehen als PR; **`/retro`** nach dem Build.

Die aktuelle Knobeln-Auswertung ist vor diesem Dokument entstanden: Die Tickets sind horizontale Layer-Slices und wurden in einem Zug umgesetzt. Für künftige Features gilt die vertikale Variante.
