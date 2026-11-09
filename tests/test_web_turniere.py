from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from knobeln.application import KnobelnService
from knobeln.store import SQLiteStore
from knobeln.web.app import create_app


def _client(tmp_path: Path) -> TestClient:
    service = KnobelnService(SQLiteStore(tmp_path / "knobeln.db"))
    return TestClient(create_app(service))


def test_start_ohne_api_key_und_ohne_turnier(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = _client(tmp_path)

    response = client.get("/scannen")

    assert response.status_code == 200
    assert "Noch kein Turnier" in response.text
    assert "Turnier anlegen" in response.text


def test_turnier_anlegen_und_umbenennen(tmp_path: Path):
    client = _client(tmp_path)

    response = client.post("/turniere", data={"name": "Sommerfest 2026"})
    assert response.status_code == 200
    assert "Sommerfest 2026" in response.text

    turnier_id = _turnier_id(client, "Sommerfest 2026")
    response = client.post(
        f"/turniere/{turnier_id}/umbenennen",
        data={"name": "Herbstfest"},
    )
    assert response.status_code == 200
    assert "Herbstfest" in response.text
    assert 'value="Sommerfest 2026"' not in response.text


def test_loeschen_braucht_bestaetigung_und_legt_sicherung_an(tmp_path: Path):
    client = _client(tmp_path)
    client.post("/turniere", data={"name": "Sommerfest 2026"})
    turnier_id = _turnier_id(client, "Sommerfest 2026")

    bestaetigung = client.get(f"/turniere/{turnier_id}/loeschen")
    assert bestaetigung.status_code == 200
    assert "Wirklich löschen" in bestaetigung.text
    assert "Sommerfest 2026" in bestaetigung.text

    response = client.post(f"/turniere/{turnier_id}/loeschen")

    assert response.status_code == 200
    assert "Noch kein Turnier" in response.text
    assert list(tmp_path.glob("knobeln.db.*.bak"))


def test_auswaehlen_ueber_http_und_neustart(tmp_path: Path):
    db = tmp_path / "knobeln.db"
    service = KnobelnService(SQLiteStore(db))
    client = TestClient(create_app(service))
    client.post("/turniere", data={"name": "Erstes"})
    client.post("/turniere", data={"name": "Zweites"})
    erstes_id = _turnier_id(client, "Erstes")

    response = client.post(f"/turniere/{erstes_id}/oeffnen")

    assert response.status_code == 200
    assert "Aktuelles Turnier: Erstes" in response.text

    neuer_client = TestClient(create_app(KnobelnService(SQLiteStore(db))))
    response = neuer_client.get("/scannen")

    assert response.status_code == 200
    assert "Aktuelles Turnier: Erstes" in response.text
    assert "Zweites" in response.text


def _turnier_id(client: TestClient, name: str) -> int:
    liste = client.get("/scannen")
    pattern = re.compile(
        r'data-turnier-id="(\d+)"\s+data-turnier-name="' + re.escape(name) + '"'
    )
    match = pattern.search(liste.text)
    assert match is not None, f"Turnier {name!r} nicht gefunden"
    return int(match.group(1))
