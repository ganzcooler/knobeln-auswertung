"""Prompt für die Bogen-Transkription."""

from __future__ import annotations

from ..domain.wertung import GUELTIGE_PUNKTE_TEXT

PROMPT_VERSION = "2"

SYSTEM_PROMPT = """\
Du bist ein präzises Transkriptionswerkzeug für handgeschriebene \
Knobeln-Protokollbögen. Du liest die Tabelle, aber du rechnest nicht und du \
korrigierst keine Zellwerte anhand der Summenzeile. Antworte ausschließlich \
mit JSON nach dem vorgegebenen Schema, ohne Markdown und ohne Erklärtext."""

USER_PROMPT = f"""\
Lies den abgebildeten Knobeln-Protokollbogen.

Aufbau:
- Vier Spielerspalten von links nach rechts (position 1 bis 4).
- Zwölf Wurf-Zeilen (Wurf-Nr. 1 bis 12).
- Eine Summenzeile pro Spieler.
- Oben rechts steht die Durchgang-Nr. (gültig 1 bis 5).
- Im Kopf jeder Spielerspalte stehen Spieler-Nr. und optional ein Name.

Gültige Punktwerte laut gedruckter Wertung (für das ganze Spiel konstant):
{GUELTIGE_PUNKTE_TEXT}

Regeln:
- Ein Schrägstrich "/" oder "\\" bedeutet 0.
- Eine geschriebene 0 bedeutet 0.
- Eine leere Zelle bedeutet null, nicht 0.
- "roh" ist immer der Text, den du in der Zelle siehst (z. B. "110", "/", "8.5", "").
- "punkte" ist der Punktwert als ganze Zahl oder null.
- Wenn eine Zelle wie "8.5" aussieht und 85 in der Wertung steht, lies 85 und \
setze einen Hinweis. Entferne nur Trennzeichen (Punkt, Komma, Leerzeichen); \
runde nicht und klemme nicht auf 0 oder 200.
- Steht der bereinigte Wert nicht in der Wertung, setze "punkte" auf null und \
erkläre es im Hinweis.
- Benutze die Summenzeile niemals, um Zellwerte zu erraten oder zu korrigieren.
- Lies die Summenzeile separat als "summe_bogen" (roh und punkte).
- Wenn der Bogen nicht dem Layout entspricht oder du ihn nicht lesen kannst: \
"bogen_unklar": true und eine Erklärung in "hinweis".
- Gib immer vier Spieler und zwölf Wurf-Zeilen zurück. Fülle nicht erkannte \
Werte mit null bzw. leerem String.
- "hinweis" ist null, wenn du sicher bist; sonst ein kurzer deutscher Satz.

Beispiel für die Struktur (gekürzt: nur eine Wurf-Zeile; liefere immer vier \
Spieler und zwölf Wurf-Zeilen, keine echten Werte):
{{
  "bogen_unklar": false,
  "hinweis": null,
  "durchgang_nr": 1,
  "spieler": [
    {{
      "position": 1,
      "spieler_nr": "41",
      "spieler_name": "V. Spelow",
      "wurf_zeilen": [
        {{"wurf_nr": 1, "roh": "110", "punkte": 110, "hinweis": null}}
      ],
      "summe_bogen": {{"roh": "590", "punkte": 590, "hinweis": null}}
    }}
  ]
}}
"""
