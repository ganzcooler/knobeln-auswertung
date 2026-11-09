from __future__ import annotations

from pathlib import Path

import pytest

from knobeln.application import KnobelnService
from knobeln.store import SQLiteStore


def _service(tmp_path: Path) -> KnobelnService:
    return KnobelnService(SQLiteStore(tmp_path / "knobeln.db"))


def test_turnier_anlegen_und_wiederfinden(tmp_path: Path):
    service = _service(tmp_path)

    turnier = service.create_turnier("Sommerfest 2026")

    assert turnier.name == "Sommerfest 2026"
    assert [t.name for t in service.list_turniere()] == ["Sommerfest 2026"]
    assert service.get_turnier(turnier.id).name == "Sommerfest 2026"


def test_umbenennen_und_leerer_name(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Sommerfest 2026")

    umbenannt = service.rename_turnier(turnier.id, "  Herbstfest  ")

    assert umbenannt.name == "Herbstfest"
    assert service.get_turnier(turnier.id).name == "Herbstfest"
    with pytest.raises(ValueError):
        service.rename_turnier(turnier.id, "   ")


def test_zuletzt_geoeffnetes_turnier_ueberlebt_neustart(tmp_path: Path):
    service = _service(tmp_path)
    erstes = service.create_turnier("Erstes")
    zweites = service.create_turnier("Zweites")

    service.open_turnier(erstes.id)
    neuer_service = _service(tmp_path)

    assert neuer_service.last_opened_turnier() == erstes
    assert service.get_turnier(zweites.id).name == "Zweites"


def test_loeschen_legt_sicherung_an_und_entfernt_turnier(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Sommerfest 2026")

    service.delete_turnier(turnier.id)

    assert service.list_turniere() == []
    assert list(tmp_path.glob("knobeln.db.*.bak"))
    assert service.last_opened_turnier() is None
