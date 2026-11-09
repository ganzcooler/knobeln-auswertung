from __future__ import annotations

import copy
import io
from pathlib import Path

import pytest
from conftest import FAKE_RESPONSES, FakeLLMClient
from openpyxl import load_workbook
from PIL import Image

from knobeln.application import DuplicateScanError, KnobelnService
from knobeln.store import SQLiteStore

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _service(
    tmp_path: Path,
    client: FakeLLMClient | None = None,
    *,
    with_llm: bool = True,
) -> KnobelnService:
    return KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=client or (FakeLLMClient() if with_llm else None),
        scan_dir=tmp_path / "scans",
    )


def _durchgang(service: KnobelnService, nummer: int = 1):
    turnier = service.create_turnier("Testturnier")
    return service.create_durchgang(turnier.id, nummer), turnier


def _import(service: KnobelnService, name: str, durchgang_id: int):
    return service.import_scan(
        dateiname=name,
        data=(EXAMPLES / name).read_bytes(),
        durchgang_id=durchgang_id,
    )


def test_scan_lesen_pruefen_abschliessen_und_rangliste(tmp_path: Path):
    service = _service(tmp_path)
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 2)

    bogen = _import(service, "img1.jpg", durchgang.id)
    assert len(bogen) == 1
    assert service.list_bogen(durchgang.id)[0].job_status == "warten"

    assert service.process_pending_jobs() == 1
    gelesen = service.list_bogen(durchgang.id)[0]
    assert gelesen.job_status == "fertig"
    assert len(service.list_gruppen_for_bogen(gelesen.id)) == 4
    assert service.list_prueffaelle(durchgang.id) == []

    service.bogen_bestaetigen(gelesen.id)
    rangliste = service.durchgang_rangliste(durchgang.id)
    assert [row.summe for row in rangliste] == [985, 775, 685, 470]
    assert rangliste[0].rang == 1

    service.close_durchgang(durchgang.id)
    assert service.get_durchgang(durchgang.id).status == "abgeschlossen"
    assert service.durchgang_rangliste(durchgang.id)[0].status == "bestätigt"
    with pytest.raises(ValueError):
        _import(service, "img1.jpg", durchgang.id)

    service.reopen_durchgang(durchgang.id)
    assert service.get_durchgang(durchgang.id).status == "offen"
    assert list(tmp_path.glob("knobeln.db.*.bak"))
    assert service.gesamt_rangliste(turnier.id)[0].spieler_nr == "41"


def test_summenfall_korrigieren_und_bestaetigen(tmp_path: Path):
    service = _service(tmp_path)
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 3)
    bogen = _import(service, "img2.jpg", durchgang.id)[0]
    service.process_pending_jobs()

    faelle = service.list_prueffaelle(durchgang.id)
    assert any(fall.art == "summe" for fall in faelle)

    gruppe = next(
        stored
        for stored in service.list_gruppen_for_bogen(bogen.id)
        if stored.gruppe.spieler_nr == "17"
    )
    with pytest.raises(ValueError):
        service.korrigiere_wert(gruppe.id, 8, 115)
    service.korrigiere_wert(gruppe.id, 8, 110)
    assert service.has_undo()
    assert service.undo_letzte_korrektur()
    assert service.get_gruppe(gruppe.id).gruppe.punkte[7] == 100
    service.korrigiere_wert(gruppe.id, 8, 110)

    assert all(
        fall.art != "summe"
        for fall in service.list_prueffaelle(durchgang.id)
        if fall.gruppe_id == gruppe.id
    )
    service.bogen_bestaetigen(bogen.id)
    assert service.list_prueffaelle(durchgang.id) == []
    service.close_durchgang(durchgang.id)


def test_summenabweichung_akzeptieren(tmp_path: Path):
    service = _service(tmp_path)
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 3)
    bogen = _import(service, "img2.jpg", durchgang.id)[0]
    service.process_pending_jobs()
    gruppe = next(
        stored
        for stored in service.list_gruppen_for_bogen(bogen.id)
        if stored.gruppe.spieler_nr == "17"
    )

    service.summe_akzeptieren(gruppe.id)

    assert service.list_prueffaelle(durchgang.id) == []
    service.bogen_bestaetigen(bogen.id)
    service.close_durchgang(durchgang.id)


def test_gleichstand_ergibt_geteilten_rang(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    durchgang, _ = _durchgang(service)
    service.create_manual_result(
        durchgang_id=durchgang.id, spieler_nr="1", spieler_name="", summe=500
    )
    service.create_manual_result(
        durchgang_id=durchgang.id, spieler_nr="2", spieler_name="", summe=500
    )

    rows = service.durchgang_rangliste(durchgang.id)

    assert [row.rang for row in rows] == [1, 1]
    assert all(row.geteilter_rang for row in rows)


def test_manuell_lehnt_vorhandenen_scan_ab(tmp_path: Path):
    service = _service(tmp_path)
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 2)
    _import(service, "img1.jpg", durchgang.id)
    service.process_pending_jobs()

    with pytest.raises(ValueError):
        service.create_manual_result(
            durchgang_id=durchgang.id,
            spieler_nr="41",
            spieler_name="",
            summe=985,
        )


def test_manuelle_ergebnisse_validierung_und_rangliste(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    durchgang, _ = _durchgang(service)

    with pytest.raises(ValueError):
        service.create_manual_result(
            durchgang_id=durchgang.id,
            spieler_nr="42",
            spieler_name="Dano",
            summe=763,
        )

    manual = service.create_manual_result(
        durchgang_id=durchgang.id,
        spieler_nr="42",
        spieler_name="Dano",
        summe=760,
    )
    service.create_manual_result(
        durchgang_id=durchgang.id,
        spieler_nr="7",
        spieler_name="",
        summe=800,
    )
    service.update_manual_result(manual.id, summe=770, spieler_name="Dano E.")

    rangliste = service.durchgang_rangliste(durchgang.id)
    assert [(row.spieler_nr, row.summe, row.quelle) for row in rangliste] == [
        ("7", 800, "manuell"),
        ("42", 770, "manuell"),
    ]
    assert rangliste[1].spieler_name == "Dano E."
    service.close_durchgang(durchgang.id)


def test_konflikt_bei_gleichen_punkten_aber_abweichender_summe(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["summe_bogen"] = {
        "roh": "990",
        "punkte": 990,
        "hinweis": None,
    }
    service = _service(tmp_path, FakeLLMClient(responses))
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 2)
    _import(service, "img1.jpg", durchgang.id)
    service.import_scan(
        dateiname="img1-kopie.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
        force=True,
    )
    service.process_pending_jobs()

    assert len(service.list_offene_konflikte(durchgang.id)) == 1
    assert all(
        stored.ergebnis_status != "aktiv"
        for stored in service.list_gruppen(durchgang.id)
        if stored.gruppe.spieler_nr == "41"
    )


def test_konflikt_bleibt_bis_entscheidung_offen(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    service = _service(tmp_path, FakeLLMClient(responses))
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 2)

    _import(service, "img1.jpg", durchgang.id)
    service.import_scan(
        dateiname="img1-kopie.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
        force=True,
    )
    service.process_pending_jobs()

    konflikte = service.store.list_offene_konflikte(durchgang.id)
    assert len(konflikte) == 1
    assert any(
        fall.art == "konflikt" for fall in service.list_prueffaelle(durchgang.id)
    )
    with pytest.raises(ValueError):
        service.close_durchgang(durchgang.id)

    service.konflikt_entscheiden(konflikte[0].id, konflikte[0].gruppe_a_id)
    assert service.store.list_offene_konflikte(durchgang.id) == []
    assert any(
        row.spieler_nr == "41" for row in service.durchgang_rangliste(durchgang.id)
    )


def test_kostenlimit_stoppt_weitere_extraktion(tmp_path: Path):
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=FakeLLMClient(),
        scan_dir=tmp_path / "scans",
        max_cost=0.0005,
    )
    _, turnier = _durchgang(service)
    durchgang = service.create_durchgang(turnier.id, 2)
    _import(service, "img1.jpg", durchgang.id)
    service.import_scan(
        dateiname="img1-kopie.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
        force=True,
    )

    assert service.process_pending_jobs() == 1
    assert [bogen.job_status for bogen in service.list_bogen(durchgang.id)] == [
        "fertig",
        "warten",
    ]


def test_offline_import_wartet_und_lokale_arbeit_bleibt_moeglich(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    durchgang, _ = _durchgang(service)

    _import(service, "img1.jpg", durchgang.id)
    assert service.process_pending_jobs() == 0
    assert service.list_bogen(durchgang.id)[0].job_status == "warten"
    assert service.connection_status() == "nicht erreichbar"

    service.create_manual_result(
        durchgang_id=durchgang.id,
        spieler_nr="42",
        spieler_name="",
        summe=760,
    )
    assert service.durchgang_rangliste(durchgang.id)[0].spieler_nr == "42"


def test_doppelter_scan_wird_erkannt_und_kann_behalten_werden(tmp_path: Path):
    service = _service(tmp_path)
    durchgang, _ = _durchgang(service)
    _import(service, "img1.jpg", durchgang.id)

    with pytest.raises(DuplicateScanError):
        _import(service, "img1.jpg", durchgang.id)

    _import_list = service.import_scan(
        dateiname="img1.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
        force=True,
    )
    assert len(_import_list) == 1
    assert len(service.list_bogen(durchgang.id)) == 2


def test_pdf_mehrseiter_und_xlsx_export(tmp_path: Path):
    service = _service(tmp_path)
    durchgang, turnier = _durchgang(service)
    first = Image.new("RGB", (40, 60), "white")
    second = Image.new("RGB", (40, 60), "gray")
    stream = io.BytesIO()
    first.save(stream, format="PDF", save_all=True, append_images=[second])
    bogen = service.import_scan(
        dateiname="mehrseiter.pdf",
        data=stream.getvalue(),
        durchgang_id=durchgang.id,
    )
    assert len(bogen) == 2
    service.process_pending_jobs()

    data = service.export_xlsx(turnier.id)
    workbook = load_workbook(io.BytesIO(data))
    assert "Gesamt" in workbook.sheetnames
    assert "Durchgang 1" in workbook.sheetnames
    assert [cell.value for cell in workbook["Gesamt"][1]] == [
        "Rang",
        "Spieler-Nr.",
        "Name",
        "Summe",
        "Quelle",
        "Status",
    ]
