from __future__ import annotations

import shutil
from pathlib import Path

from conftest import FakeLLMClient
from typer.testing import CliRunner

from knobeln.application import KnobelnService
from knobeln.cli import app
from knobeln.store import SQLiteStore

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "web" in result.output
    assert "import" in result.output


def test_version():
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "knobeln-auswertung" in result.output


def test_import_command(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copy(EXAMPLES / "img1.jpg", input_dir / "img1.jpg")
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=FakeLLMClient(),
        scan_dir=tmp_path / "scans",
    )
    monkeypatch.setattr("knobeln.cli.build_service", lambda **kwargs: service)

    result = CliRunner().invoke(
        app,
        [
            "import",
            str(input_dir),
            "--db",
            str(tmp_path / "knobeln.db"),
            "--scans",
            str(tmp_path / "scans"),
            "--turnier",
            "Testturnier",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "1 Bogen" in result.output
    turnier = service.list_turniere()[0]
    durchgang = service.list_durchgaenge(turnier.id)[0]
    assert len(service.list_bogen(durchgang.id)) == 1


def test_web_command_startet_web_ui(tmp_path: Path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_run_server(db_path=None, *, scan_dir=None, port=8000):
        calls["db_path"] = db_path
        calls["scan_dir"] = scan_dir
        calls["port"] = port

    monkeypatch.setattr("knobeln.cli.run_server", fake_run_server)
    db = tmp_path / "knobeln.db"

    result = CliRunner().invoke(app, ["web", "--db", str(db)])

    assert result.exit_code == 0, result.output
    assert calls["db_path"] == db


def test_ohne_argument_startet_web(tmp_path: Path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_run_server(db_path=None, *, scan_dir=None, port=8000):
        calls["db_path"] = db_path

    monkeypatch.setattr("knobeln.cli.run_server", fake_run_server)

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0, result.output
    assert calls["db_path"] is None


def test_server_bindet_nur_localhost(tmp_path: Path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_uvicorn_run(app, *, host, port):
        calls["host"] = host
        calls["port"] = port

    monkeypatch.setattr("knobeln.web.server.uvicorn.run", fake_uvicorn_run)

    from knobeln.web.server import run_server

    run_server(
        tmp_path / "knobeln.db",
        scan_dir=tmp_path / "scans",
        port=8765,
    )

    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8765
