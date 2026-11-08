"""Abbildung zwischen CSV-Zeilen und Domänengruppen."""

from __future__ import annotations

from typing import Any

from ..domain.models import BogenRef, Gruppe
from ..domain.normalize import as_text, normalize_summe, parse_int
from ..domain.wertung import ist_gueltige_summe


def gruppe_from_csv_rows(
    rows: list[dict[str, Any]],
    unknown_columns: list[str] | None = None,
) -> Gruppe:
    rows = [r for r in rows if r]
    unknown_columns = unknown_columns or []
    punkte: list[int | None] = [None] * 12
    roh: list[str] = [""] * 12
    korrekturen: list[str | None] = [None] * 12
    kommentare = [""] * 12
    extra_by_wurf: dict[int | None, dict[str, str]] = {}

    for row in rows:
        wurf = parse_int(row.get("Wurf_Nr"))
        idx = (wurf - 1) if wurf is not None and 1 <= wurf <= 12 else None
        if idx is not None:
            punkte[idx] = parse_int(row.get("Punkte"))
            roh[idx] = as_text(row.get("Punkte_Roh"))
            note = as_text(row.get("Korrektur"))
            korrekturen[idx] = note or None
            kommentare[idx] = as_text(row.get("Kommentar"))

        extra = {
            column: as_text(row.get(column))
            for column in unknown_columns
            if as_text(row.get(column))
        }
        if extra:
            extra_by_wurf.setdefault(wurf if idx is not None else None, {}).update(
                extra
            )
        if idx is None:
            kommentar = as_text(row.get("Kommentar"))
            if kommentar and not kommentare[0]:
                kommentare[0] = kommentar

    summe_roh = _first_nonempty(rows, "Summe_Bogen_Roh")
    summe_text = _first_nonempty(rows, "Summe_Bogen")
    summe_bogen = parse_int(summe_text)
    if summe_bogen is None:
        if summe_text:
            summe_status = "summe_ungueltig"
        elif summe_roh:
            raw_norm = normalize_summe(summe_roh, None)
            summe_status = (
                "summe_ungueltig"
                if raw_norm.status == "summe_ungueltig"
                else "summe_fehlt"
            )
        else:
            summe_status = "summe_fehlt"
    elif not ist_gueltige_summe(summe_bogen):
        summe_status = "summe_ungueltig"
    elif summe_roh and _summe_wurde_korrigiert(summe_roh, summe_bogen):
        summe_status = "summe_korrigiert"
    else:
        summe_status = None

    name_conflicts: set[str] = set()
    for row in rows:
        for part in as_text(row.get("Namenskonflikt")).split("|"):
            if part.strip():
                name_conflicts.add(part.strip())

    status_text = _first_nonempty(rows, "Status")
    if "identitaet_konflikt" in status_text:
        konflikt_art = "identitaet"
    elif "konflikt" in status_text:
        konflikt_art = "daten"
    else:
        konflikt_art = ""

    ref = BogenRef(
        bogen_id=_first_nonempty(rows, "Bogen_ID"),
        quelle=_first_nonempty(rows, "Quelle"),
        seite=parse_int(_first_nonempty(rows, "Seite")) or 1,
    )
    gruppe = Gruppe(
        ref=ref,
        position=parse_int(_first_nonempty(rows, "Spieler_Position")) or 0,
        durchgang_nr=parse_int(_first_nonempty(rows, "Durchgang_Nr")),
        spieler_nr=_first_nonempty(rows, "Spieler_Nr"),
        spieler_name=_first_nonempty(rows, "Spieler_Name"),
        punkte=punkte,
        punkte_roh=roh,
        korrekturen=korrekturen,
        summe_bogen=summe_bogen,
        summe_bogen_roh=summe_roh,
        summe_bogen_status=summe_status,
        konflikt=any(as_text(r.get("Konflikt")) == "ja" for r in rows),
        konflikt_art=konflikt_art,
        konflikt_detail=_first_nonempty(rows, "Konflikt_Detail"),
        geprueft=any(as_text(r.get("Geprueft")) == "ja" for r in rows),
        kommentare=kommentare,
        name_conflict_names=name_conflicts,
        extra_by_wurf=extra_by_wurf,
        placeholder=any("bogen_unklar" in as_text(r.get("Status")) for r in rows),
    )
    gruppe.recompute()
    return gruppe


def gruppe_to_rows(
    gruppe: Gruppe,
    fieldnames: list[str],
) -> list[dict[str, str]]:
    if gruppe.placeholder:
        return [_row(gruppe, fieldnames, wurf_nr=None)]

    return [_row(gruppe, fieldnames, wurf_nr=i + 1) for i in range(12)]


def _row(
    gruppe: Gruppe,
    fieldnames: list[str],
    wurf_nr: int | None,
) -> dict[str, str]:
    idx = (wurf_nr - 1) if wurf_nr is not None else None
    values = {
        "Bogen_ID": gruppe.bogen_id,
        "Quelle": gruppe.quelle,
        "Seite": str(gruppe.seite),
        "Spieler_Position": str(gruppe.position) if gruppe.position else "",
        "Durchgang_Nr": (
            "" if gruppe.durchgang_nr is None else str(gruppe.durchgang_nr)
        ),
        "Spieler_Nr": gruppe.spieler_nr,
        "Spieler_Name": gruppe.spieler_name,
        "Wurf_Nr": "" if wurf_nr is None else str(wurf_nr),
        "Punkte": "",
        "Punkte_Roh": "",
        "Korrektur": "",
        "Summe_Bogen_Roh": gruppe.summe_bogen_roh,
        "Summe_Bogen": ("" if gruppe.summe_bogen is None else str(gruppe.summe_bogen)),
        "Summe_Berechnet": (
            "" if gruppe.summe_berechnet is None else str(gruppe.summe_berechnet)
        ),
        "Delta": "" if gruppe.delta is None else str(gruppe.delta),
        "Status": gruppe.status_text,
        "Warnung": gruppe.warnung_text,
        "Konflikt": "ja" if gruppe.konflikt else "nein",
        "Konflikt_Detail": gruppe.konflikt_detail,
        "Namenskonflikt": " | ".join(sorted(gruppe.name_conflict_names)),
        "Geprueft": "ja" if gruppe.geprueft else "nein",
        "Kommentar": (
            gruppe.kommentare[idx]
            if idx is not None
            else (gruppe.kommentare[0] if gruppe.kommentare else "")
        ),
    }
    if idx is not None:
        values["Punkte"] = "" if gruppe.punkte[idx] is None else str(gruppe.punkte[idx])
        values["Punkte_Roh"] = gruppe.punkte_roh[idx]
        values["Korrektur"] = gruppe.korrekturen[idx] or ""
    extra = gruppe.extra_by_wurf.get(wurf_nr if wurf_nr is not None else None, {})
    return {name: values.get(name, extra.get(name, "")) for name in fieldnames}


def _summe_wurde_korrigiert(raw: str, value: int) -> bool:
    norm = normalize_summe(raw, value)
    return norm.summe == value and norm.korrektur is not None


def _first_nonempty(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        value = as_text(row.get(key))
        if value:
            return value
    return ""
