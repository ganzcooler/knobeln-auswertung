from knobeln.domain.normalize import normalize_punkte, normalize_summe


def test_slash_ist_null():
    assert normalize_punkte("/", None).punkte == 0
    assert normalize_punkte("\\", None).punkte == 0
    assert normalize_punkte("0", 0).punkte == 0


def test_trennzeichen_artefakte():
    assert normalize_punkte("8.5", None).punkte == 85
    assert normalize_punkte("10.5", None).punkte == 105
    assert normalize_punkte("1.5", None).punkte == 15
    assert normalize_punkte("8.0", None).punkte == 80
    assert normalize_punkte("8.5", 85).status == "wert_korrigiert"
    assert normalize_punkte("8.5", 85).korrektur


def test_ungueltige_werte_werden_nicht_gerundet_oder_geklemmt():
    assert normalize_punkte("115", 115).punkte is None
    assert normalize_punkte("115", 115).status == "wert_ungueltig"
    assert normalize_punkte("87", 87).punkte is None
    assert normalize_punkte("205", 205).punkte is None
    assert normalize_punkte("-5", -5).punkte is None


def test_leere_zelle_ist_fehlt():
    assert normalize_punkte("", None).status == "wert_fehlt"
    assert normalize_punkte(None, None).status == "wert_fehlt"
    # Ein LLM-Kandidat darf eine leere Zelle nicht heimlich füllen.
    leer = normalize_punkte("", 105)
    assert leer.punkte is None
    assert leer.status == "wert_fehlt"


def test_geschriebene_null_ohne_llm_kandidat():
    assert normalize_punkte("0", None).punkte == 0
    assert normalize_punkte("0.0", None).punkte == 0
    assert normalize_summe("0", None).summe == 0
    assert normalize_summe("", 765).summe is None
    assert normalize_summe("", 765).status == "summe_fehlt"


def test_llm_normalisierung_wird_markiert():
    result = normalize_punkte("1O5", 105)
    assert result.punkte == 105
    assert result.status == "wert_korrigiert"
    assert "LLM" in (result.korrektur or "")


def test_summe():
    assert normalize_summe("765", 765).summe == 765
    assert normalize_summe("7.65", 765).summe == 765
    assert normalize_summe("7.65", 765).status == "summe_korrigiert"
    assert normalize_summe("", None).status == "summe_fehlt"
    assert normalize_summe("766", 766).status == "summe_ungueltig"
    assert normalize_summe("2400", 2400).summe == 2400
    assert normalize_summe("2405", 2405).summe is None
    assert normalize_summe("0", 0).summe == 0
