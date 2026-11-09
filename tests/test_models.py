import copy

import pytest
from conftest import FAKE_RESPONSES
from pydantic import ValidationError

from knobeln.domain.models import BogenRef, Gruppe
from knobeln.llm.mapping import build_neue_bogen, gruppe_from_llm
from knobeln.llm.models import BogenLLM, SpielerLLM


def _spieler(name: str, position: int) -> SpielerLLM:
    data = FAKE_RESPONSES[name]
    return SpielerLLM.model_validate(data["spieler"][position - 1])


def test_summe_stimmt_bei_img():
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img.jpg", 1),
        durchgang_nr=1,
        spieler=_spieler("img.jpg", 4),
        position=4,
    )
    assert gruppe.summe_berechnet == 935
    assert gruppe.delta == 0
    assert "summe_abweichung" not in gruppe.statuses
    assert "wert_korrigiert" in gruppe.statuses


def test_summenabweichung_bei_img2():
    gruppe = gruppe_from_llm(
        ref=BogenRef("b2-p1", "img2.jpg", 1),
        durchgang_nr=1,
        spieler=_spieler("img2.jpg", 1),
        position=1,
    )
    assert gruppe.summe_berechnet == 755
    assert gruppe.summe_bogen == 765
    assert gruppe.delta == 10
    assert "summe_abweichung" in gruppe.statuses
    assert "765" in gruppe.warnung_text
    assert "755" in gruppe.warnung_text


def test_fehlende_und_ungueltige_werte():
    spieler = SpielerLLM.model_validate(
        {
            "position": 1,
            "spieler_nr": "1",
            "spieler_name": None,
            "wurf_zeilen": [
                {
                    "wurf_nr": i,
                    "roh": "" if i == 1 else ("115" if i == 2 else "10"),
                    "punkte": None if i == 1 else (115 if i == 2 else 10),
                    "hinweis": None,
                }
                for i in range(1, 13)
            ],
            "summe_bogen": {"roh": "100", "punkte": 100, "hinweis": None},
        }
    )
    gruppe = gruppe_from_llm(
        ref=BogenRef("b", "x", 1),
        durchgang_nr=1,
        spieler=spieler,
        position=1,
    )
    assert "wert_fehlt" in gruppe.statuses
    assert "wert_ungueltig" in gruppe.statuses
    assert gruppe.summe_berechnet is None
    assert "summe_unvollstaendig" in gruppe.statuses


def test_ungueltiger_wert_macht_summe_unvollstaendig():
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img1.jpg", 1),
        durchgang_nr=2,
        spieler=_spieler("img1.jpg", 1),
        position=1,
    )
    gruppe.punkte[0] = 115
    gruppe.recompute()
    assert "wert_ungueltig" in gruppe.statuses
    assert gruppe.summe_berechnet is None
    assert "summe_unvollstaendig" in gruppe.statuses


def test_platzhalter():
    gruppe = Gruppe(
        ref=BogenRef("b", "x", 1),
        position=0,
        durchgang_nr=None,
        spieler_nr="",
        spieler_name="",
        placeholder=True,
    )
    gruppe.recompute()
    assert gruppe.status_text == "bogen_unklar"
    assert "nicht gelesen" in gruppe.warnung_text


def test_ungueltige_summe_wird_als_summe_ungueltig_gemeldet():
    spieler = _spieler("img1.jpg", 1)
    spieler.summe_bogen.roh = "766"
    spieler.summe_bogen.punkte = None
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img1.jpg", 1),
        durchgang_nr=2,
        spieler=spieler,
        position=1,
    )
    assert gruppe.summe_bogen is None
    assert "summe_ungueltig" in gruppe.statuses
    assert "summe_fehlt" not in gruppe.statuses


def test_zu_viele_wurf_zeilen_werden_abgelehnt():
    data = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    data["spieler"][0]["wurf_zeilen"] = data["spieler"][0]["wurf_zeilen"] * 3
    with pytest.raises(ValidationError):
        BogenLLM.model_validate(data)


def test_doppelte_position_wird_abgelehnt():
    data = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    data["spieler"][1]["position"] = 1
    with pytest.raises(ValidationError):
        BogenLLM.model_validate(data)


def test_bogen_unklar_darf_ohne_spieler_sein():
    bogen = BogenLLM.model_validate(
        {
            "bogen_unklar": True,
            "hinweis": "nicht lesbar",
            "durchgang_nr": None,
            "spieler": [],
        }
    )
    assert bogen.bogen_unklar is True


def test_build_neue_bogen_hat_vier_spieler():
    response = BogenLLM.model_validate(FAKE_RESPONSES["img.jpg"])
    bogen = build_neue_bogen(
        response,
        ref=BogenRef("b-p1", "img.jpg", 1),
    )
    assert len(bogen.spieler) == 4
    assert bogen.bogen_unklar is False
