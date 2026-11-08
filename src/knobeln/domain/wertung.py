"""Die gedruckte Wertung ist für das gesamte Spiel konstant."""

from __future__ import annotations

WERTUNG_NACH_WURF: dict[str, int] = {
    "104": 5,
    "105": 10,
    "106": 15,
    "107": 20,
    "108": 25,
    "109": 30,
    "110": 35,
    "122": 40,
    "123": 45,
    "124": 50,
    "125": 55,
    "162": 60,
    "163": 65,
    "164": 70,
    "165": 75,
    "202": 80,
    "203": 85,
    "204": 90,
    "205": 95,
    "220": 100,
    "260": 105,
    "300": 110,
    "222*": 120,
    "333*": 130,
    "444*": 140,
    "555*": 150,
    "666*": 160,
    "111*": 170,
    "123*": 200,
}

# 0 ist der Sonderwert für Schrägstrich/Fehlwurf und steht nicht in der Tabelle.
GUELTIGE_PUNKTE: frozenset[int] = frozenset({0, *WERTUNG_NACH_WURF.values()})

GUELTIGE_PUNKTE_TEXT = ", ".join(str(p) for p in sorted(GUELTIGE_PUNKTE))

MAX_SUMME = 2400
SUMME_SCHRITT = 5


def ist_gueltige_summe(wert: int | None) -> bool:
    return wert is not None and 0 <= wert <= MAX_SUMME and wert % SUMME_SCHRITT == 0
