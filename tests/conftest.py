from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from knobeln.llm.models import BogenLLM
from knobeln.llm.client import LLMResult


def _player(
    position: int,
    spieler_nr: str,
    spieler_name: str,
    werte: list[int | None],
    summe: int,
    *,
    roh: dict[int, str] | None = None,
) -> dict[str, Any]:
    roh = roh or {}
    wurf_zeilen = []
    for index, wert in enumerate(werte, start=1):
        raw = roh.get(index)
        if raw is None:
            raw = "/" if wert == 0 else ("" if wert is None else str(wert))
        wurf_zeilen.append(
            {
                "wurf_nr": index,
                "roh": raw,
                "punkte": wert,
                "hinweis": None,
            }
        )
    return {
        "position": position,
        "spieler_nr": spieler_nr,
        "spieler_name": spieler_name,
        "wurf_zeilen": wurf_zeilen,
        "summe_bogen": {"roh": str(summe), "punkte": summe, "hinweis": None},
    }


def _bogen(players: list[dict[str, Any]], durchgang: int = 1) -> dict[str, Any]:
    return {
        "bogen_unklar": False,
        "hinweis": None,
        "durchgang_nr": durchgang,
        "spieler": players,
    }


FAKE_RESPONSES: dict[str, dict[str, Any]] = {
    "img.jpg": _bogen(
        [
            _player(
                1,
                "43",
                "V. Spelow",
                [110, 0, 95, 120, 85, 80, 25, 60, 15, 0, 0, 0],
                590,
            ),
            _player(
                2,
                "9",
                "",
                [95, 105, 25, 110, 105, 80, 110, 130, 25, 0, 0, 10],
                795,
            ),
            _player(
                3,
                "42",
                "",
                [105, 65, 105, 110, 85, 25, 80, 15, 95, 75, 0, 0],
                760,
            ),
            _player(
                4,
                "2",
                "D. U.-E.",
                [85, 150, 30, 110, 100, 95, 15, 105, 110, 25, 110, 0],
                935,
                roh={1: "8.5", 6: "9.5"},
            ),
        ],
        durchgang=1,
    ),
    "img1.jpg": _bogen(
        [
            _player(
                1,
                "41",
                "V. Spelow",
                [110, 15, 95, 120, 85, 80, 25, 60, 200, 100, 95, 0],
                985,
            ),
            _player(
                2,
                "46",
                "Steffen",
                [25, 65, 105, 25, 60, 200, 105, 95, 95, 0, 0, 0],
                775,
            ),
            _player(
                3,
                "32",
                "Angelika",
                [85, 60, 15, 100, 95, 20, 95, 0, 0, 0, 0, 0],
                470,
            ),
            _player(
                4,
                "4",
                "",
                [110, 110, 25, 20, 80, 105, 140, 70, 25, 0, 0, 0],
                685,
            ),
        ],
        durchgang=2,
    ),
    "img2.jpg": _bogen(
        [
            _player(
                1,
                "17",
                "",
                [200, 60, 95, 105, 20, 80, 95, 100, 0, 0, 0, 0],
                765,
            ),
            _player(
                2,
                "48",
                "",
                [200, 170, 75, 5, 200, 20, 60, 110, 25, 15, 200, 0],
                1080,
            ),
            _player(
                3,
                "25",
                "",
                [105, 25, 50, 85, 95, 130, 80, 85, 80, 0, 0, 0],
                735,
            ),
            _player(
                4,
                "30",
                "",
                [65, 35, 70, 90, 90, 45, 90, 95, 65, 0, 0, 0],
                645,
            ),
        ],
        durchgang=3,
    ),
}


class FakeLLMClient:
    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        self.responses = responses or FAKE_RESPONSES
        self.calls: list[str] = []

    def extract_bogen(
        self,
        *,
        bogen_id: str,
        quelle: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> LLMResult:
        name = Path(quelle).name
        self.calls.append(name)
        data = self.responses[name]
        return LLMResult(
            bogen=BogenLLM.model_validate(data),
            prompt_tokens=100,
            completion_tokens=50,
            reasoning_tokens=40,
            cost_usd=0.001,
        )


def write_test_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (30, 40), "white")
    image.save(path, format="JPEG")


@pytest.fixture
def fake_client() -> FakeLLMClient:
    return FakeLLMClient()
