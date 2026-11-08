"""Querschnittsprüfungen über mehrere Spielergruppen."""

from __future__ import annotations

from collections import defaultdict

from .models import Gruppe


def apply_identity_checks(groups: list[Gruppe]) -> None:
    """Namens-Kanonisierung und Doppelungen innerhalb eines Bogens."""
    for gruppe in groups:
        gruppe.clear_extras()

    namen: dict[str, set[str]] = defaultdict(set)
    for gruppe in groups:
        if not gruppe.spieler_nr:
            continue
        if gruppe.spieler_name:
            namen[gruppe.spieler_nr].add(gruppe.spieler_name)
        if gruppe.name_conflict_names:
            namen[gruppe.spieler_nr].update(gruppe.name_conflict_names)

    for nummer, namensmenge in namen.items():
        if len(namensmenge) == 1:
            kanonisch = next(iter(namensmenge))
            for gruppe in groups:
                if gruppe.spieler_nr == nummer:
                    gruppe.name_conflict_names.clear()
                    if not gruppe.spieler_name:
                        gruppe.spieler_name = kanonisch
        else:
            lesbar = ", ".join(repr(n) for n in sorted(namensmenge))
            for gruppe in groups:
                if gruppe.spieler_nr == nummer:
                    gruppe.zusatz_status.add("name_konflikt")
                    gruppe.zusatz_warnungen.append(
                        f"Namenskonflikt für Spieler {nummer}: {lesbar}."
                    )

    pro_bogen: dict[tuple[str, str], list[Gruppe]] = defaultdict(list)
    for gruppe in groups:
        if gruppe.bogen_id and gruppe.spieler_nr:
            pro_bogen[(gruppe.bogen_id, gruppe.spieler_nr)].append(gruppe)

    for (_, nummer), gruppen in pro_bogen.items():
        if len(gruppen) > 1:
            for gruppe in gruppen:
                gruppe.zusatz_status.add("spieler_doppelt")
                gruppe.zusatz_warnungen.append(
                    f"Spieler-Nr. {nummer} kommt auf diesem Bogen mehrfach vor."
                )

    for gruppe in groups:
        gruppe.recompute()


def offene_gruppen(groups: list[Gruppe]) -> list[Gruppe]:
    return [gruppe for gruppe in groups if gruppe.ist_offen()]


def gruppen_nach_bogen(groups: list[Gruppe]) -> dict[str, list[Gruppe]]:
    result: dict[str, list[Gruppe]] = defaultdict(list)
    for gruppe in groups:
        result[gruppe.bogen_id].append(gruppe)
    return result
