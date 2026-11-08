import copy

import pytest
from conftest import FAKE_RESPONSES
from pydantic import ValidationError

from knobeln.domain.models import BogenRef, Gruppe
from knobeln.io.csv_mapping import gruppe_from_csv_rows, gruppe_to_rows
from knobeln.llm.mapping import build_neue_bogen, gruppe_from_llm
from knobeln.llm.models import BogenLLM, SpielerLLM

CSV_FIELDS = [
    "Bogen_ID", "Quelle", "Seite", "Spieler_Position", "Durchgang_Nr",
    "Spieler_Nr", "Spieler_Name", "Wurf_Nr", "Punkte", "Punkte_Roh",
    "Korrektur", "Summe_Bogen_Roh", "Summe_Bogen", "Summe_Berechnet",
    "Delta", "Status", "Warnung", "Konflikt", "Konflikt_Detail",
    "Namenskonflikt", "Geprueft", "Kommentar",
]


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


def test_csv_roundtrip():
    data = FAKE_RESPONSES["img2.jpg"]
    spieler = SpielerLLM.model_validate(data["spieler"][0])
    gruppe = gruppe_from_llm(
        ref=BogenRef("b", "img2.jpg", 1),
        durchgang_nr=1,
        spieler=spieler,
        position=1,
    )
    gruppe.geprueft = True
    gruppe.konflikt = True
    gruppe.konflikt_detail = "W01: bestehend 200, neu 195"
    gruppe.name_conflict_names = {"V. Spelow", "V. Spellow"}
    gruppe.kommentare[0] = "geprüft"
    gruppe.recompute()
    rows = gruppe_to_rows(gruppe, CSV_FIELDS)
    wieder = gruppe_from_csv_rows(rows)
    assert wieder.punkte == gruppe.punkte
    assert wieder.summe_bogen == 765
    assert wieder.konflikt is True
    assert wieder.geprueft is True
    assert wieder.name_conflict_names == {"V. Spelow", "V. Spellow"}
    assert wieder.kommentare[0] == "geprüft"
    assert "summe_abweichung" in wieder.statuses
    assert "konflikt" in wieder.statuses
    assert "geprueft" in wieder.statuses


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


def test_ungueltige_summe_aus_csv():
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img1.jpg", 1),
        durchgang_nr=2,
        spieler=_spieler("img1.jpg", 1),
        position=1,
    )
    rows = gruppe_to_rows(gruppe, CSV_FIELDS)
    for row in rows:
        row["Summe_Bogen"] = "abc"
    wieder = gruppe_from_csv_rows(rows)
    assert wieder.summe_bogen is None
    assert "summe_ungueltig" in wieder.statuses
    assert "summe_fehlt" not in wieder.statuses


def test_ungueltige_summe_bleibt_nach_roundtrip_ungueltig():
    spieler = _spieler("img1.jpg", 1)
    spieler.summe_bogen.roh = "766"
    spieler.summe_bogen.punkte = None
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img1.jpg", 1),
        durchgang_nr=2,
        spieler=spieler,
        position=1,
    )
    wieder = gruppe_from_csv_rows(gruppe_to_rows(gruppe, CSV_FIELDS))
    assert wieder.summe_bogen is None
    assert "summe_ungueltig" in wieder.statuses
    assert "summe_fehlt" not in wieder.statuses


def test_kommentare_bleiben_pro_zeile():
    gruppe = gruppe_from_llm(
        ref=BogenRef("b1-p1", "img1.jpg", 1),
        durchgang_nr=2,
        spieler=_spieler("img1.jpg", 1),
        position=1,
    )
    gruppe.kommentare[0] = "Wurf 1 geprüft"
    gruppe.kommentare[1] = "Wurf 2 anders"
    wieder = gruppe_from_csv_rows(gruppe_to_rows(gruppe, CSV_FIELDS))
    assert wieder.kommentare[0] == "Wurf 1 geprüft"
    assert wieder.kommentare[1] == "Wurf 2 anders"
    assert wieder.kommentare[2] == ""


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
