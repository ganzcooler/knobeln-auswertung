from __future__ import annotations

import copy
import io
from pathlib import Path

import pytest
from conftest import FAKE_RESPONSES, FakeLLMClient
from openpyxl import load_workbook

from knobeln.application import KnobelnService
from knobeln.llm.client import LLMError, LLMJSONError
from knobeln.store import SQLiteStore

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _service(
    tmp_path: Path,
    client: FakeLLMClient | None = None,
) -> KnobelnService:
    return KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=client or FakeLLMClient(),
        scan_dir=tmp_path / "scans",
    )


def _import(service: KnobelnService, name: str, durchgang_id: int, *, force=False):
    return service.import_scan(
        dateiname=name,
        data=(EXAMPLES / name).read_bytes(),
        durchgang_id=durchgang_id,
        force=force,
    )


def test_kompletter_abend_ueber_zwei_durchgaenge(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Sommerfest")
    d2 = service.create_durchgang(turnier.id, 2)
    d3 = service.create_durchgang(turnier.id, 3)

    _import(service, "img1.jpg", d2.id)
    service.process_pending_jobs()
    bogen1 = service.list_bogen(d2.id)[0]
    service.bogen_bestaetigen(bogen1.id)

    _import(service, "img2.jpg", d3.id)
    service.process_pending_jobs()
    bogen2 = service.list_bogen(d3.id)[0]
    gruppe17 = next(
        stored
        for stored in service.list_gruppen_for_bogen(bogen2.id)
        if stored.gruppe.spieler_nr == "17"
    )
    service.korrigiere_wert(gruppe17.id, 8, 110)
    service.bogen_bestaetigen(bogen2.id)

    service.create_manual_result(
        durchgang_id=d2.id,
        spieler_nr="99",
        spieler_name="Dano",
        summe=500,
    )

    assert [row.summe for row in service.durchgang_rangliste(d2.id)] == [
        985,
        775,
        685,
        500,
        470,
    ]
    gesamt = {row.spieler_nr: row.summe for row in service.gesamt_rangliste(turnier.id)}
    assert gesamt["41"] == 985
    assert gesamt["17"] == 765
    assert gesamt["99"] == 500

    service.close_durchgang(d2.id)
    service.close_durchgang(d3.id)
    assert all(
        row.status == "bestätigt" for row in service.gesamt_rangliste(turnier.id)
    )

    workbook = load_workbook(io.BytesIO(service.export_xlsx(turnier.id)))
    assert {"Durchgang 2", "Durchgang 3", "Gesamt"} <= set(workbook.sheetnames)


def test_extraktion_fehler_retry_und_netz_wartet(tmp_path: Path):
    class FlakyClient:
        def __init__(self) -> None:
            self.calls = 0
            self.fallback = FakeLLMClient()

        def extract_bogen(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise LLMJSONError("kaputte Antwort")
            return self.fallback.extract_bogen(**kwargs)

    flaky = FlakyClient()
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=flaky,
        scan_dir=tmp_path / "scans",
    )
    turnier = service.create_turnier("Retry")
    durchgang = service.create_durchgang(turnier.id, 2)
    _import(service, "img1.jpg", durchgang.id)

    assert service.process_pending_jobs() == 0
    assert service.list_bogen(durchgang.id)[0].job_status == "fehler"

    service.retry_bogen(service.list_bogen(durchgang.id)[0].id)
    assert service.process_pending_jobs() == 1
    assert service.list_bogen(durchgang.id)[0].job_status == "fertig"

    class OfflineClient:
        def extract_bogen(self, **kwargs):
            raise LLMError("Verbindung weg")

    zweiter = service.create_durchgang(turnier.id, 3)
    _import(service, "img2.jpg", zweiter.id)
    service.llm_client = OfflineClient()
    assert service.process_pending_jobs() == 0
    assert service.list_bogen(zweiter.id)[0].job_status == "warten"

    service.llm_client = FakeLLMClient()
    assert service.process_pending_jobs() == 1
    assert service.list_bogen(zweiter.id)[0].job_status == "fertig"


def test_alle_pruefaktionen_und_blockaden(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Aktionen")
    durchgang = service.create_durchgang(turnier.id, 1)
    _import(service, "img.jpg", durchgang.id)
    service.process_pending_jobs()
    bogen = service.list_bogen(durchgang.id)[0]
    gruppe = next(
        stored
        for stored in service.list_gruppen_for_bogen(bogen.id)
        if stored.gruppe.spieler_nr == "2"
    )

    korrektur = next(
        fall
        for fall in service.list_prueffaelle(durchgang.id)
        if fall.gruppe_id == gruppe.id and fall.art == "wert_korrigiert"
    )
    service.uebernehme_wert(gruppe.id, korrektur.wurf_nr or 1)
    assert all(
        not (fall.gruppe_id == gruppe.id and fall.wurf_nr == korrektur.wurf_nr)
        for fall in service.list_prueffaelle(durchgang.id)
    )
    with pytest.raises(ValueError):
        service.korrigiere_wert(gruppe.id, 2, 115)
    service.markiere_unleserlich(gruppe.id, 2)
    gespeichert = service.get_gruppe(gruppe.id)
    assert "Als unleserlich markiert" in gespeichert.gruppe.kommentare[1]
    with pytest.raises(ValueError):
        service.bogen_bestaetigen(bogen.id)


def test_manuell_gegen_scan_konflikt_und_spaeterer_scan(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    service = _service(tmp_path, FakeLLMClient(responses))
    turnier = service.create_turnier("Konflikt")
    durchgang = service.create_durchgang(turnier.id, 2)
    service.create_manual_result(
        durchgang_id=durchgang.id,
        spieler_nr="41",
        spieler_name="Manuell",
        summe=500,
    )
    _import(service, "img1.jpg", durchgang.id)
    service.process_pending_jobs()

    konflikt = service.list_offene_konflikte(durchgang.id)[0]
    scan_gruppe = next(
        stored
        for stored in service.list_gruppen(durchgang.id)
        if stored.id in {konflikt.gruppe_a_id, konflikt.gruppe_b_id}
        and stored.quelle == "scan"
    )
    service.konflikt_entscheiden(konflikt.id, scan_gruppe.id)
    assert service.list_offene_konflikte(durchgang.id) == []
    assert any(
        stored.ergebnis_status == "verworfen" and stored.quelle == "manuell"
        for stored in service.list_gruppen(durchgang.id)
    )
    assert any(
        row.spieler_nr == "41" and row.summe == 985
        for row in service.durchgang_rangliste(durchgang.id)
    )

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


def test_gesamtwertung_ueber_mehrere_durchgaenge(tmp_path: Path):
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=None,
        scan_dir=tmp_path / "scans",
    )
    turnier = service.create_turnier("Gesamt")
    d1 = service.create_durchgang(turnier.id, 1)
    d2 = service.create_durchgang(turnier.id, 2)
    service.create_manual_result(
        durchgang_id=d1.id, spieler_nr="1", spieler_name="A", summe=500
    )
    service.create_manual_result(
        durchgang_id=d2.id, spieler_nr="1", spieler_name="A", summe=600
    )
    service.create_manual_result(
        durchgang_id=d1.id, spieler_nr="2", spieler_name="B", summe=700
    )
    service.create_manual_result(
        durchgang_id=d2.id, spieler_nr="2", spieler_name="B", summe=100
    )

    gesamt = service.gesamt_rangliste(turnier.id)
    assert [(row.spieler_nr, row.summe, row.rang) for row in gesamt] == [
        ("1", 1100, 1),
        ("2", 800, 2),
    ]

    service.close_durchgang(d1.id)
    service.close_durchgang(d2.id)
    assert all(
        row.status == "bestätigt" for row in service.gesamt_rangliste(turnier.id)
    )


def test_prueffaelle_nach_schweregrad_sortiert(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img2-kaputt.jpg"] = copy.deepcopy(FAKE_RESPONSES["img2.jpg"])
    responses["img2-kaputt.jpg"]["spieler"][1]["wurf_zeilen"][0]["punkte"] = 115
    responses["img2-kaputt.jpg"]["spieler"][1]["wurf_zeilen"][0]["roh"] = "115"
    service = _service(tmp_path, FakeLLMClient(responses))
    turnier = service.create_turnier("Sortierung")
    durchgang = service.create_durchgang(turnier.id, 3)
    service.import_scan(
        dateiname="img2-kaputt.jpg",
        data=(EXAMPLES / "img2.jpg").read_bytes(),
        durchgang_id=durchgang.id,
    )
    service.process_pending_jobs()

    faelle = service.list_prueffaelle(durchgang.id)
    assert faelle[0].art == "summe"
    assert any(fall.art == "wert_ungueltig" for fall in faelle)
    assert faelle.index(next(f for f in faelle if f.art == "summe")) < faelle.index(
        next(f for f in faelle if f.art == "wert_ungueltig")
    )


def test_offline_zu_online_nach_verbindungspruefung(tmp_path: Path):
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=None,
        scan_dir=tmp_path / "scans",
    )
    turnier = service.create_turnier("Offline")
    durchgang = service.create_durchgang(turnier.id, 2)
    _import(service, "img1.jpg", durchgang.id)
    assert service.process_pending_jobs() == 0
    assert service.list_bogen(durchgang.id)[0].job_status == "warten"

    service.llm_client = FakeLLMClient()
    assert service.process_pending_jobs() == 1
    assert service.list_bogen(durchgang.id)[0].job_status == "fertig"
