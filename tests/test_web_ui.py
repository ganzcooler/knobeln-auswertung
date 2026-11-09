from __future__ import annotations

import copy
import io
from pathlib import Path

from conftest import FAKE_RESPONSES, FakeLLMClient
from fastapi.testclient import TestClient
from PIL import Image

from knobeln.application import KnobelnService
from knobeln.store import SQLiteStore
from knobeln.web.app import create_app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _service(
    tmp_path: Path,
    *,
    responses: dict | None = None,
    with_llm: bool = True,
) -> KnobelnService:
    client = FakeLLMClient(responses) if with_llm else None
    return KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=client,
        scan_dir=tmp_path / "scans",
    )


def _setup(
    tmp_path: Path,
    nummer: int = 1,
    *,
    responses: dict | None = None,
    with_llm: bool = True,
):
    service = _service(tmp_path, responses=responses, with_llm=with_llm)
    turnier = service.create_turnier("UI-Turnier")
    durchgang = service.create_durchgang(turnier.id, nummer)
    return service, turnier, durchgang, TestClient(create_app(service))


def _upload(client: TestClient, name: str):
    return client.post(
        "/bogen/upload",
        files={
            "dateien": (
                name,
                (EXAMPLES / name).read_bytes(),
                "image/jpeg",
            )
        },
    )


def _group(service: KnobelnService, durchgang_id: int, spieler_nr: str):
    return next(
        stored
        for stored in service.list_gruppen(durchgang_id)
        if stored.gruppe.spieler_nr == spieler_nr and stored.quelle == "scan"
    )


def test_scannen_leer_hilfe_und_static(tmp_path: Path):
    _, _, _, client = _setup(tmp_path, with_llm=False)

    response = client.get("/scannen")

    assert response.status_code == 200
    assert "Noch keine Bögen" in response.text
    assert "Der Dienst ist gerade nicht erreichbar" in response.text
    assert 'id="hilfe-dialog"' in response.text
    assert client.get("/static/htmx.min.js").status_code == 200
    assert client.get("/static/app.css").status_code == 200


def test_durchgang_anlegen_auswaehlen_und_fortschritt(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=2)

    _upload(client, "img1.jpg")
    response = client.get("/scannen")

    assert response.status_code == 200
    assert "1 von 1 Bögen gelesen" in response.text
    assert "Bogen bestätigen" in response.text
    assert "Durchgang 2" in response.text
    aktuell = service.current_durchgang(service.list_turniere()[0].id)
    assert aktuell is not None
    assert aktuell.id == durchgang.id


def test_clean_bogen_aus_scannen_bestaetigen(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=2)
    _upload(client, "img1.jpg")
    bogen = service.list_bogen(durchgang.id)[0]

    response = client.post(f"/bogen/{bogen.id}/bestaetigen")

    assert response.status_code == 200
    assert "Bogen bestätigt" in response.text
    assert service.list_prueffaelle(durchgang.id) == []


def test_upload_fehler_und_duplikat_bleiben_sichtbar(tmp_path: Path):
    _, _, _, client = _setup(tmp_path, nummer=2)

    fehler = client.post(
        "/bogen/upload",
        files={"dateien": ("notiz.txt", b"kein scan", "text/plain")},
    )
    assert "Bitte JPG, PNG oder PDF" in fehler.text

    _upload(client, "img1.jpg")
    doppelt = _upload(client, "img1.jpg")
    assert "scheint schon im Stapel" in doppelt.text


def test_pdf_upload_erzeugt_zwei_boegen_im_stapel(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=2)
    first = Image.new("RGB", (40, 60), "white")
    second = Image.new("RGB", (40, 60), "gray")
    stream = io.BytesIO()
    first.save(stream, format="PDF", save_all=True, append_images=[second])

    response = client.post(
        "/bogen/upload",
        files={"dateien": ("mehrseiter.pdf", stream.getvalue(), "application/pdf")},
    )

    assert response.status_code == 200
    assert len(service.list_bogen(durchgang.id)) == 2


def test_scan_bild_und_zoom_button(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=1)
    _upload(client, "img.jpg")
    bogen = service.list_bogen(durchgang.id)[0]

    bild = client.get(f"/bogen/{bogen.id}/scan")
    pruefen = client.get("/pruefen")

    assert bild.status_code == 200
    assert bild.headers["content-type"].startswith("image/jpeg")
    assert "Zoom umschalten" in pruefen.text
    assert "Zulässige Werte" in pruefen.text
    assert "Vorschlag" in pruefen.text


def test_queue_filter_und_leerer_filter(tmp_path: Path):
    _, _, durchgang, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")

    summe = client.get("/pruefen?art=summe")
    konflikt = client.get("/pruefen?art=konflikt")

    assert "Summe stimmt nicht" in summe.text
    assert "Keine Fälle in diesem Filter" in konflikt.text
    assert "Spieler 17" in summe.text


def test_pruefentscheidung_und_undo(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")
    gruppe = _group(service, durchgang.id, "17")

    response = client.post(
        "/pruefen/aktion",
        data={
            "aktion": "korrigieren",
            "gruppe_id": gruppe.id,
            "wurf_nr": 8,
            "wert": 110,
        },
    )
    assert "Gespeichert" in response.text
    assert service.get_gruppe(gruppe.id).gruppe.punkte[7] == 110

    undo = client.post("/pruefen/undo")
    assert "rückgängig" in undo.text
    assert service.get_gruppe(gruppe.id).gruppe.punkte[7] == 100


def test_summe_akzeptieren_und_abschliessen(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")
    gruppe = _group(service, durchgang.id, "17")

    blocked = client.post(f"/durchgang/{durchgang.id}/abschliessen")
    assert "offene Prüffälle" in blocked.text

    client.post(
        "/pruefen/aktion",
        data={"aktion": "summe_akzeptieren", "gruppe_id": gruppe.id},
    )
    response = client.post(f"/durchgang/{durchgang.id}/abschliessen")

    assert "Bestätigt" in response.text
    assert service.get_durchgang(durchgang.id).status == "abgeschlossen"


def test_kopfzeile_korrigieren(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=1)
    _upload(client, "img1.jpg")
    gruppe = _group(service, durchgang.id, "41")

    assert any(
        fall.gruppe_id == gruppe.id and fall.art == "kopfzeile"
        for fall in service.list_prueffaelle(durchgang.id)
    )
    response = client.post(
        "/pruefen/aktion",
        data={
            "aktion": "kopf_korrigieren",
            "gruppe_id": gruppe.id,
            "spieler_nr": "41",
        },
    )

    assert "Gespeichert" in response.text
    assert all(
        not (fall.gruppe_id == gruppe.id and fall.art == "kopfzeile")
        for fall in service.list_prueffaelle(durchgang.id)
    )


def test_unleserlich_markieren(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")
    gruppe = _group(service, durchgang.id, "17")

    response = client.post(
        "/pruefen/aktion",
        data={"aktion": "unleserlich", "gruppe_id": gruppe.id, "wurf_nr": 1},
    )

    assert "Gespeichert" in response.text
    gespeichert = service.get_gruppe(gruppe.id)
    assert gespeichert.gruppe.punkte[0] is None
    assert "Als unleserlich markiert" in gespeichert.gruppe.kommentare[0]


def test_konflikt_ueber_http_entscheiden(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    service, _, durchgang, client = _setup(tmp_path, nummer=2, responses=responses)
    _upload(client, "img1.jpg")
    client.post(
        "/bogen/upload",
        files={
            "dateien": (
                "img1-kopie.jpg",
                (EXAMPLES / "img1.jpg").read_bytes(),
                "image/jpeg",
            )
        },
        data={"force": "true"},
    )
    konflikt = service.list_offene_konflikte(durchgang.id)[0]

    response = client.post(
        "/pruefen/aktion",
        data={
            "aktion": "konflikt",
            "konflikt_id": konflikt.id,
            "gewaehlt_gruppe_id": konflikt.gruppe_a_id,
        },
    )

    assert "Gespeichert" in response.text
    assert service.list_offene_konflikte(durchgang.id) == []


def test_manuell_validieren_bearbeiten_und_rangliste(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, with_llm=False)

    invalid = client.post(
        "/manuell",
        data={"spieler_nr": "42", "spieler_name": "", "summe": "763"},
    )
    assert "durch 5 teilbar" in invalid.text

    created = client.post(
        "/manuell",
        data={"spieler_nr": "42", "spieler_name": "Dano", "summe": "760"},
    )
    assert "Manuelles Ergebnis gespeichert" in created.text
    manual = service.list_gruppen(durchgang.id)[0]

    edited = client.post(
        f"/manuell/{manual.id}/bearbeiten",
        data={"spieler_nr": "42", "spieler_name": "Dano E.", "summe": "770"},
    )
    assert "Manuelles Ergebnis geändert" in edited.text
    assert service.durchgang_rangliste(durchgang.id)[0].summe == 770


def test_rangliste_vollbild_gleichstand_und_export(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, with_llm=False)
    service.create_manual_result(
        durchgang_id=durchgang.id, spieler_nr="1", spieler_name="", summe=500
    )
    service.create_manual_result(
        durchgang_id=durchgang.id, spieler_nr="2", spieler_name="", summe=500
    )

    response = client.get("/rangliste?vollbild=1")
    export = client.get("/rangliste/export.xlsx")

    assert "geteilter Rang" in response.text
    assert "Vollbild beenden" in response.text
    assert export.status_code == 200
    assert export.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_rangliste_leerzustand(tmp_path: Path):
    _, _, _, client = _setup(tmp_path, with_llm=False)

    response = client.get("/rangliste")

    assert response.status_code == 200
    assert "Noch keine bestätigten Ergebnisse" in response.text


def test_abschliessen_wieder_oeffnen_mit_bestaetigung(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, with_llm=False)
    client.post(f"/durchgang/{durchgang.id}/abschliessen")

    response = client.get("/rangliste")

    assert 'onsubmit="return confirm' in response.text
    assert "wieder öffnen" in response.text
    client.post(f"/durchgang/{durchgang.id}/wieder-oeffnen")
    assert service.get_durchgang(durchgang.id).status == "offen"


def test_verbindung_pruefen_und_offline_banner(tmp_path: Path):
    _, _, _, client = _setup(tmp_path, with_llm=False)

    seite = client.get("/scannen")
    response = client.post("/verbindung/pruefen")

    assert "Der Dienst ist gerade nicht erreichbar" in seite.text
    assert response.status_code == 200
    assert "Verbindungsstatus aktualisiert" in response.text


def test_startup_verarbeitet_wartende_jobs(tmp_path: Path):
    service = _service(tmp_path)
    turnier = service.create_turnier("Startup")
    durchgang = service.create_durchgang(turnier.id, 2)
    service.import_scan(
        dateiname="img1.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
    )

    with TestClient(create_app(service)) as client:
        response = client.get("/scannen")

    assert response.status_code == 200
    assert service.list_bogen(durchgang.id)[0].job_status == "fertig"


def test_fehlende_spielerposition_erzeugt_keine_prueffaelle(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-leer.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-leer.jpg"]["spieler"][3] = {
        "position": 4,
        "spieler_nr": "",
        "spieler_name": None,
        "wurf_zeilen": [
            {"wurf_nr": i, "roh": "", "punkte": None, "hinweis": None}
            for i in range(1, 13)
        ],
        "summe_bogen": {"roh": "", "punkte": None, "hinweis": None},
    }
    service, _, durchgang, client = _setup(tmp_path, nummer=2, responses=responses)

    client.post(
        "/bogen/upload",
        files={
            "dateien": (
                "img1-leer.jpg",
                (EXAMPLES / "img1.jpg").read_bytes(),
                "image/jpeg",
            )
        },
    )

    assert len(service.list_gruppen(durchgang.id)) == 3
    assert service.list_prueffaelle(durchgang.id) == []


def test_ungueltige_korrektur_zeigt_fehler(tmp_path: Path):
    service, _, durchgang, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")
    gruppe = _group(service, durchgang.id, "17")

    response = client.post(
        "/pruefen/aktion",
        data={
            "aktion": "korrigieren",
            "gruppe_id": gruppe.id,
            "wurf_nr": 8,
            "wert": 115,
        },
    )

    assert "nicht in der Wertung" in response.text


def test_exportfehler_wird_angezeigt(tmp_path: Path, monkeypatch):
    service, _, _, client = _setup(tmp_path, with_llm=False)

    def kaputt(_turnier_id):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(service, "export_xlsx", kaputt)
    response = client.get("/rangliste/export.xlsx")

    assert "Export fehlgeschlagen" in response.text


def test_scan_404_und_accessibility_markup(tmp_path: Path):
    _, _, _, client = _setup(tmp_path, nummer=3)
    _upload(client, "img2.jpg")

    assert client.get("/bogen/999/scan").status_code == 404
    pruefen = client.get("/pruefen")
    scannen = client.get("/scannen")
    css = client.get("/static/app.css").text

    assert 'aria-live="polite"' in pruefen.text
    assert "event.key === '?'" in scannen.text
    assert "min-height: 44px" in css
    assert "prefers-reduced-motion" in css


def test_verbindung_pruefen_verarbeitet_wartende_jobs(tmp_path: Path):
    service = _service(tmp_path, with_llm=False)
    turnier = service.create_turnier("Verbindung")
    durchgang = service.create_durchgang(turnier.id, 2)
    service.import_scan(
        dateiname="img1.jpg",
        data=(EXAMPLES / "img1.jpg").read_bytes(),
        durchgang_id=durchgang.id,
    )
    client = TestClient(create_app(service))

    service.llm_client = FakeLLMClient()
    response = client.post("/verbindung/pruefen")

    assert response.status_code == 200
    assert service.list_bogen(durchgang.id)[0].job_status == "fertig"


def test_summenstatus_erzeugt_prueffall(tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-ohne-summe.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-ohne-summe.jpg"]["spieler"][0]["summe_bogen"] = {
        "roh": "",
        "punkte": None,
        "hinweis": None,
    }
    service, _, durchgang, client = _setup(tmp_path, nummer=2, responses=responses)

    client.post(
        "/bogen/upload",
        files={
            "dateien": (
                "img1-ohne-summe.jpg",
                (EXAMPLES / "img1.jpg").read_bytes(),
                "image/jpeg",
            )
        },
    )

    assert any(
        fall.art == "summe" and "Summenzeile" in fall.titel
        for fall in service.list_prueffaelle(durchgang.id)
    )
