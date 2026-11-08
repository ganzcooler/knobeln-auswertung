from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from conftest import FAKE_RESPONSES, FakeLLMClient, write_test_image
from PIL import Image

from knobeln.config import Config
from knobeln.llm.models import BogenLLM
from knobeln.io.csv_store import CSVWriteError, load_groups, read_rows, write_groups
from knobeln.llm.client import LLMResult
from knobeln.pipeline import Pipeline, PipelineError

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _config(tmp_path: Path, **kwargs) -> Config:
    return Config(
        input_dir=tmp_path / "input",
        output_csv=tmp_path / "auswertung.csv",
        review_dir=tmp_path / "review",
        model="deepseek/deepseek-v4.1-flash",
        reasoning="max",
        api_key="dummy",
        **kwargs,
    )


def _copy_examples(input_dir: Path, names: list[str]) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy(EXAMPLES / name, input_dir / name)


def _rows_by_player(path: Path) -> dict[str, list[dict[str, str]]]:
    rows, _ = read_rows(path)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["Spieler_Nr"], []).append(row)
    return grouped


def test_pipeline_drei_beispiele(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img.jpg", "img1.jpg", "img2.jpg"])
    config = _config(tmp_path)
    client = FakeLLMClient()

    summary = Pipeline(config, client).run()

    assert summary.files_total == 3
    assert summary.pages_processed == 3
    assert summary.new_groups == 12
    assert summary.open_groups == 2
    assert summary.deleted == 1
    assert summary.moved == 2
    assert summary.exit_code == 2
    assert len(summary.file_costs) == 3
    assert sum(cost.prompt_tokens for cost in summary.file_costs) == 300
    assert sum(cost.completion_tokens for cost in summary.file_costs) == 150

    groups, _ = load_groups(config.output_csv)
    assert len(groups) == 12
    by_nr = _rows_by_player(config.output_csv)
    assert "17" in by_nr
    assert any("summe_abweichung" in row["Status"] for row in by_nr["17"])
    assert all(row["Delta"] == "10" for row in by_nr["17"])

    img_rows = by_nr["2"]
    assert any("wert_korrigiert" in row["Status"] for row in img_rows)
    assert not any("summe_abweichung" in row["Status"] for row in img_rows)
    assert any("8.5 -> 85" in row["Korrektur"] for row in img_rows)

    assert not (tmp_path / "input" / "img1.jpg").exists()
    assert (tmp_path / "review" / "img.jpg").exists()
    assert (tmp_path / "review" / "img2.jpg").exists()


def test_zweiter_lauf_ueberspringt_bekannte_datei(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path)
    Pipeline(config, FakeLLMClient()).run()
    assert not (tmp_path / "input" / "img1.jpg").exists()

    _copy_examples(tmp_path / "input", ["img1.jpg"])
    client = FakeLLMClient()
    summary = Pipeline(config, client).run()

    assert summary.files_skipped == 1
    assert client.calls == []
    assert summary.deleted == 1
    assert not (tmp_path / "input" / "img1.jpg").exists()


def test_konflikt_bei_gleichem_spieler_und_durchgang(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path)
    Pipeline(config, FakeLLMClient()).run()

    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    write_test_image(tmp_path / "input" / "img1-kopie.jpg")

    client = FakeLLMClient(responses)
    summary = Pipeline(config, client).run()

    assert summary.conflicts == 1
    assert summary.new_groups == 0
    groups, _ = load_groups(config.output_csv)
    assert len(groups) == 4
    p41 = next(g for g in groups if g.spieler_nr == "41")
    assert p41.punkte[0] == 110
    assert p41.konflikt is True
    assert "W01" in p41.konflikt_detail
    assert (tmp_path / "review" / "img1-kopie.jpg").exists()


def test_keep_input_verhindert_review_move(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    Pipeline(_config(tmp_path), FakeLLMClient()).run()

    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    write_test_image(tmp_path / "input" / "img1-kopie.jpg")

    config = _config(tmp_path, keep_input=True)
    summary = Pipeline(config, FakeLLMClient(responses)).run()

    assert summary.conflicts == 1
    assert summary.moved == 0
    assert summary.kept == 1
    assert (tmp_path / "input" / "img1-kopie.jpg").exists()
    assert not (tmp_path / "review" / "img1-kopie.jpg").exists()


def test_technischer_fehler_bleibt_im_eingang(tmp_path: Path):
    from knobeln.llm.client import LLMError

    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path)

    class FailingClient:
        def extract_bogen(self, **kwargs):
            raise LLMError("Testfehler")

    summary = Pipeline(config, FailingClient()).run()

    assert summary.technical_errors == 1
    assert summary.kept == 1
    assert summary.exit_code == 2
    assert (tmp_path / "input" / "img1.jpg").exists()
    assert config.output_csv.exists()
    rows, _ = read_rows(config.output_csv)
    assert rows == []


def test_korrektur_ueber_die_csv_clear_summenwarnung(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img2.jpg"])
    config = _config(tmp_path)
    Pipeline(config, FakeLLMClient()).run()

    groups, fields = load_groups(config.output_csv)
    p17 = next(g for g in groups if g.spieler_nr == "17")
    assert "summe_abweichung" in p17.statuses
    p17.punkte[7] = 110  # 100 -> 110: Summe 765 statt 755
    p17.recompute()
    write_groups(config.output_csv, groups, fields)

    summary = Pipeline(config, FakeLLMClient()).run()

    assert summary.open_groups == 0
    groups2, _ = load_groups(config.output_csv)
    p17_neu = next(g for g in groups2 if g.spieler_nr == "17")
    assert "summe_abweichung" not in p17_neu.statuses
    assert p17_neu.status_text == "ok"


def test_geprueft_akzeptiert_summenabweichung(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img2.jpg"])
    config = _config(tmp_path)
    Pipeline(config, FakeLLMClient()).run()

    groups, fields = load_groups(config.output_csv)
    p17 = next(g for g in groups if g.spieler_nr == "17")
    p17.geprueft = True
    p17.recompute()
    write_groups(config.output_csv, groups, fields)

    summary = Pipeline(config, FakeLLMClient()).run()

    assert summary.open_groups == 0
    groups2, _ = load_groups(config.output_csv)
    p17_neu = next(g for g in groups2 if g.spieler_nr == "17")
    assert "summe_abweichung" in p17_neu.statuses
    assert "geprueft" in p17_neu.statuses


def test_mehrseitige_pdf(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    page1 = Image.new("RGB", (40, 60), "white")
    page2 = Image.new("RGB", (40, 60), "gray")
    page1.save(
        input_dir / "scan.pdf",
        format="PDF",
        save_all=True,
        append_images=[page2],
    )

    class PdfFake:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def extract_bogen(self, *, bogen_id, quelle, image_bytes, mime_type):
            self.calls.append(bogen_id)
            data = (
                FAKE_RESPONSES["img1.jpg"]
                if len(self.calls) == 1
                else FAKE_RESPONSES["img2.jpg"]
            )
            return LLMResult(
                bogen=BogenLLM.model_validate(data),
                prompt_tokens=10,
                completion_tokens=5,
            )

    config = _config(tmp_path)
    fake = PdfFake()
    summary = Pipeline(config, fake).run()

    assert summary.pages_processed == 2
    assert summary.new_groups == 8
    assert summary.moved == 1
    assert (tmp_path / "review" / "scan.pdf").exists()

    rows, _ = read_rows(config.output_csv)
    assert {row["Seite"] for row in rows} == {"1", "2"}
    assert {row["Quelle"] for row in rows} == {"scan.pdf"}
    assert len({row["Bogen_ID"] for row in rows}) == 2


def test_dry_run_schreibt_nicht(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path, dry_run=True)
    summary = Pipeline(config, FakeLLMClient()).run()

    assert summary.deleted == 1
    assert not config.output_csv.exists()
    assert (tmp_path / "input" / "img1.jpg").exists()


def test_reset_archiviert_alte_csv(tmp_path: Path):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path)
    Pipeline(config, FakeLLMClient()).run()

    config2 = _config(tmp_path, reset=True)
    summary = Pipeline(config2, FakeLLMClient()).run()

    assert summary.new_groups == 0
    backups = list(tmp_path.glob("auswertung.*.bak.csv"))
    assert len(backups) == 1
    rows, _ = read_rows(config2.output_csv)
    assert rows == []


def test_csv_schreibfehler_laesst_eingang_unangetastet(
    tmp_path: Path, monkeypatch
):
    _copy_examples(tmp_path / "input", ["img1.jpg"])
    config = _config(tmp_path)

    def fail(*args, **kwargs):
        raise CSVWriteError("gesperrt")

    monkeypatch.setattr("knobeln.pipeline.write_groups", fail)
    with pytest.raises(PipelineError):
        Pipeline(config, FakeLLMClient()).run()

    assert (tmp_path / "input" / "img1.jpg").exists()
    assert not config.output_csv.exists()
