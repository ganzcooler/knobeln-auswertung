"""Inkrementeller Merge neuer Spielergruppen in die bestehende CSV."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Gruppe
from .validation import apply_identity_checks


@dataclass
class MergeResult:
    gruppen: list[Gruppe]
    neue_gruppen: int = 0
    duplikate: int = 0
    konflikte: int = 0
    details: list[str] = field(default_factory=list)
    conflict_bogen_ids: set[str] = field(default_factory=set)
    duplicate_bogen_ids: dict[str, str] = field(default_factory=dict)


def merge_gruppen(
    bestehende: list[Gruppe],
    eingehende: list[Gruppe],
) -> MergeResult:
    merged: list[Gruppe] = list(bestehende)
    by_bogen_pos: dict[tuple[str, int], Gruppe] = {}
    by_player: dict[tuple[int, str], list[Gruppe]] = {}

    by_placeholder: dict[str, Gruppe] = {}
    for gruppe in merged:
        by_bogen_pos.setdefault(gruppe.bogen_position_key(), gruppe)
        if gruppe.placeholder:
            by_placeholder[gruppe.bogen_id] = gruppe
        key = gruppe.player_key()
        if key is not None:
            by_player.setdefault(key, []).append(gruppe)

    result = MergeResult(gruppen=merged)

    for incoming in eingehende:
        bp_key = incoming.bogen_position_key()
        player_key = incoming.player_key()

        if not incoming.placeholder:
            placeholder = by_placeholder.get(incoming.bogen_id)
            if placeholder is not None:
                idx = next(i for i, g in enumerate(merged) if g is placeholder)
                merged[idx] = incoming
                by_bogen_pos[bp_key] = incoming
                by_placeholder.pop(incoming.bogen_id, None)
                if placeholder.extra_by_wurf:
                    extras = placeholder.extra_by_wurf.get(None, {})
                    if extras:
                        for wurf_nr in range(1, 13):
                            incoming.extra_by_wurf.setdefault(wurf_nr, {}).update(
                                extras
                            )
                if player_key is not None:
                    by_player.setdefault(player_key, []).append(incoming)
                result.neue_gruppen += 1
                continue

        existing = by_bogen_pos.get(bp_key)
        if existing is not None:
            if _identity_conflict(existing, incoming):
                detail = _identity_detail(existing, incoming)
                _mark_conflict(existing, detail, "identitaet")
                result.konflikte += 1
                result.details.append(detail)
                result.conflict_bogen_ids.add(incoming.bogen_id)
                continue

            _fill_missing_identity(existing, incoming)
            if _werte_gleich(existing, incoming):
                _merge_name_info(existing, incoming)
                result.duplikate += 1
                result.duplicate_bogen_ids[incoming.bogen_id] = existing.bogen_id
                continue

            detail = _diff_detail(existing, incoming)
            _mark_conflict(existing, detail, "daten")
            result.konflikte += 1
            result.details.append(detail)
            result.conflict_bogen_ids.add(incoming.bogen_id)
            continue

        if player_key is not None and player_key in by_player:
            vorhandene = by_player[player_key]
            if any(g.bogen_id == incoming.bogen_id for g in vorhandene):
                # Gleiche Spieler-Nr. zweimal auf demselben Bogen: beide
                # Gruppen bleiben erhalten; spieler_doppelt wird markiert.
                merged.append(incoming)
                by_bogen_pos[bp_key] = incoming
                by_player[player_key].append(incoming)
                result.neue_gruppen += 1
                continue

            if all(_werte_gleich(g, incoming) for g in vorhandene):
                for gruppe in vorhandene:
                    _merge_name_info(gruppe, incoming)
                result.duplikate += 1
                result.duplicate_bogen_ids[incoming.bogen_id] = vorhandene[0].bogen_id
                continue

            detail = _diff_detail(vorhandene[0], incoming)
            for gruppe in vorhandene:
                _mark_conflict(gruppe, detail, "daten")
            result.konflikte += 1
            result.details.append(detail)
            result.conflict_bogen_ids.add(incoming.bogen_id)
            continue

        merged.append(incoming)
        by_bogen_pos[bp_key] = incoming
        if player_key is not None:
            by_player.setdefault(player_key, []).append(incoming)
        result.neue_gruppen += 1

    apply_identity_checks(merged)
    result.gruppen = merged
    return result


def _werte_gleich(a: Gruppe, b: Gruppe) -> bool:
    return a.punkte == b.punkte and a.summe_bogen == b.summe_bogen


def _identity_conflict(a: Gruppe, b: Gruppe) -> bool:
    if a.spieler_nr and b.spieler_nr and a.spieler_nr != b.spieler_nr:
        return True
    if (
        a.durchgang_nr is not None
        and b.durchgang_nr is not None
        and a.durchgang_nr != b.durchgang_nr
    ):
        return True
    return False


def _fill_missing_identity(existing: Gruppe, incoming: Gruppe) -> None:
    if not existing.spieler_nr and incoming.spieler_nr:
        existing.spieler_nr = incoming.spieler_nr
    if existing.durchgang_nr is None and incoming.durchgang_nr is not None:
        existing.durchgang_nr = incoming.durchgang_nr
    if not existing.spieler_name and incoming.spieler_name:
        existing.spieler_name = incoming.spieler_name


def _merge_name_info(existing: Gruppe, incoming: Gruppe) -> None:
    if not incoming.spieler_name:
        return
    if not existing.spieler_name:
        existing.spieler_name = incoming.spieler_name
        return
    if incoming.spieler_name != existing.spieler_name:
        existing.name_conflict_names.update(
            {existing.spieler_name, incoming.spieler_name}
        )


def _identity_detail(a: Gruppe, b: Gruppe) -> str:
    return (
        "Identität: bestehend "
        f"D{a.durchgang_nr or '?'}/S{a.spieler_nr or '?'}, "
        f"neu D{b.durchgang_nr or '?'}/S{b.spieler_nr or '?'}"
    )


def _mark_conflict(gruppe: Gruppe, detail: str, art: str) -> None:
    gruppe.konflikt = True
    gruppe.konflikt_art = art
    gruppe.konflikt_detail = detail
    gruppe.geprueft = False


def _diff_detail(existing: Gruppe, incoming: Gruppe) -> str:
    parts: list[str] = []
    for i, (alt, neu) in enumerate(
        zip(existing.punkte, incoming.punkte, strict=True),
        start=1,
    ):
        if alt != neu:
            parts.append(
                f"W{i:02d}: bestehend {alt if alt is not None else 'leer'}, "
                f"neu {neu if neu is not None else 'leer'}"
            )
    if existing.summe_bogen != incoming.summe_bogen:
        parts.append(
            "Summe: bestehend "
            f"{existing.summe_bogen if existing.summe_bogen is not None else 'leer'}, "
            "neu "
            f"{incoming.summe_bogen if incoming.summe_bogen is not None else 'leer'}"
        )
    if not parts:
        parts.append("abweichende Werte")
    return "; ".join(parts)
