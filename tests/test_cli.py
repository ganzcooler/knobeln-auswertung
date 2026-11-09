from __future__ import annotations

import shutil
from pathlib import Path

from conftest import FakeLLMClient
from typer.testing import CliRunner

from knobeln.cli import app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "web" in result.output
    assert "run" in result.output


def test_version():
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "knobeln-auswertung" in result.output


def test_fehlender_api_key(monkeypatch):
    monkeypatch.setattr("knobeln.config.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = CliRunner().invoke(app, ["run", "--input", "input"])
    assert result.exit_code == 1
    assert "OPENROUTER_API_KEY" in result.output


def test_cli_mit_fake_client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copy(EXAMPLES / "img1.jpg", input_dir / "img1.jpg")
    output = tmp_path / "auswertung.csv"
    review = tmp_path / "review"

    fake = FakeLLMClient()
    monkeypatch.setattr("knobeln.cli.OpenRouterClient", lambda **kwargs: fake)

    result = CliRunner().invoke(
        app,
        [
            "run",
            "--input",
            str(input_dir),
            "--output",
            str(output),
            "--review",
            str(review),
            "--model",
            "deepseek/deepseek-v4.1-flash",
            "--reasoning",
            "max",
        ],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert "Zusammenfassung" in result.output


def test_web_command_startet_nur_localhost(tmp_path: Path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_run_server(db_path=None, *, host="127.0.0.1", port=8000):
        calls["db_path"] = db_path
        calls["host"] = host
        calls["port"] = port

    monkeypatch.setattr("knobeln.cli.run_server", fake_run_server)
    db = tmp_path / "knobeln.db"

    result = CliRunner().invoke(app, ["web", "--db", str(db)])

    assert result.exit_code == 0, result.output
    assert calls["host"] == "127.0.0.1"
    assert calls["db_path"] == db


def test_ohne_argument_startet_web(tmp_path: Path, monkeypatch):
    calls: dict[str, object] = {}

    def fake_run_server(db_path=None, *, host="127.0.0.1", port=8000):
        calls["db_path"] = db_path
        calls["host"] = host

    monkeypatch.setattr("knobeln.cli.run_server", fake_run_server)

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0, result.output
    assert calls["host"] == "127.0.0.1"
