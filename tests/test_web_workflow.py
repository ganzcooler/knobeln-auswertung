from __future__ import annotations

from pathlib import Path

from conftest import FakeLLMClient
from fastapi.testclient import TestClient

from knobeln.application import KnobelnService
from knobeln.store import SQLiteStore
from knobeln.web.app import create_app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _service(tmp_path: Path, *, with_llm: bool = True) -> KnobelnService:
    return KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=FakeLLMClient() if with_llm else None,
        scan_dir=tmp_path / "scans",
    )


def test_web_ablauf_upload_pruefen_rangliste_export(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Webturnier")
    service.create_durchgang(turnier.id, 3)
    client = TestClient(create_app(service))

    response = client.post(
        "/bogen/upload",
        files={
            "dateien": (
                "img2.jpg",
                (EXAMPLES / "img2.jpg").read_bytes(),
                "image/jpeg",
            )
        },
    )
    assert response.status_code == 200
    assert "fertig" in response.text
    assert "Summe stimmt nicht" in client.get("/pruefen").text
    assert "Gesamt" in client.get("/rangliste").text

    export = client.get("/rangliste/export.xlsx")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_web_manuell_hilfe_und_offline_banner(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    turnier = service.create_turnier("Webturnier")
    durchgang = service.create_durchgang(turnier.id, 1)
    client = TestClient(create_app(service))

    hilfe = client.get("/scannen")
    assert "So funktioniert es" in hilfe.text
    assert "Der Dienst ist gerade nicht erreichbar" in hilfe.text

    response = client.post(
        "/manuell",
        data={"spieler_nr": "42", "spieler_name": "Dano", "summe": "760"},
    )
    assert response.status_code == 200
    assert "760" in response.text
    assert "manuell" in response.text
    assert service.durchgang_rangliste(durchgang.id)[0].summe == 760


def test_web_durchgang_abschliessen_und_wieder_oeffnen(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    turnier = service.create_turnier("Webturnier")
    durchgang = service.create_durchgang(turnier.id, 1)
    client = TestClient(create_app(service))

    response = client.post(f"/durchgang/{durchgang.id}/abschliessen")
    assert response.status_code == 200
    assert "Bestätigt" in response.text
    assert service.get_durchgang(durchgang.id).status == "abgeschlossen"

    response = client.post(f"/durchgang/{durchgang.id}/wieder-oeffnen")
    assert response.status_code == 200
    assert service.get_durchgang(durchgang.id).status == "offen"


def test_web_konflikt_ansicht(tmp_path: Path):
    import copy

    from conftest import FAKE_RESPONSES

    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=FakeLLMClient(responses),
        scan_dir=tmp_path / "scans",
    )
    turnier = service.create_turnier("Webturnier")
    durchgang = service.create_durchgang(turnier.id, 2)
    service.import_scan(
        dateiname="img1.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
    )
    service.import_scan(
        dateiname="img1-kopie.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
        force=True,
    )
    service.process_pending_jobs()
    konflikt = service.store.list_offene_konflikte(durchgang.id)[0]
    client = TestClient(create_app(service))

    response = client.get(f"/pruefen?fall=k{konflikt.id}")

    assert response.status_code == 200
    assert "Konflikt bei Spieler 41" in response.text
    assert "Diese Erfassung gilt" in response.text
