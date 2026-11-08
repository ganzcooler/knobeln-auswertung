from conftest import FAKE_RESPONSES

from knobeln.domain.merge import merge_gruppen
from knobeln.domain.models import BogenRef, Gruppe
from knobeln.domain.validation import apply_identity_checks
from knobeln.llm.mapping import gruppe_from_llm
from knobeln.llm.models import SpielerLLM


def _gruppe(
    name: str,
    position: int,
    *,
    bogen_id: str = "b1-p1",
    durchgang: int = 1,
) -> Gruppe:
    data = FAKE_RESPONSES[name]
    spieler = SpielerLLM.model_validate(data["spieler"][position - 1])
    return gruppe_from_llm(
        ref=BogenRef(bogen_id, name, 1),
        durchgang_nr=durchgang,
        spieler=spieler,
        position=position,
    )


def test_neue_gruppe_wird_angehaengt():
    result = merge_gruppen([], [_gruppe("img1.jpg", 1)])
    assert result.neue_gruppen == 1
    assert len(result.gruppen) == 1


def test_duplikat_wird_uebersprungen():
    existing = _gruppe("img1.jpg", 1, bogen_id="alt")
    incoming = _gruppe("img1.jpg", 1, bogen_id="neu")
    result = merge_gruppen([existing], [incoming])
    assert result.duplikate == 1
    assert result.neue_gruppen == 0
    assert len(result.gruppen) == 1
    assert result.gruppen[0].bogen_id == "alt"


def test_konflikt_ueberschreibt_nicht():
    existing = _gruppe("img1.jpg", 1, bogen_id="alt")
    incoming = _gruppe("img1.jpg", 1, bogen_id="neu")
    incoming.punkte[0] = 100
    incoming.recompute()

    result = merge_gruppen([existing], [incoming])
    assert result.konflikte == 1
    assert result.neue_gruppen == 0
    assert result.gruppen[0].punkte[0] == 110
    assert result.gruppen[0].konflikt is True
    assert "W01" in result.gruppen[0].konflikt_detail


def test_menschliche_korrektur_bleibt():
    existing = _gruppe("img1.jpg", 1, bogen_id="alt")
    existing.punkte[0] = 100
    existing.recompute()

    incoming = _gruppe("img1.jpg", 1, bogen_id="neu")
    result = merge_gruppen([existing], [incoming])
    assert result.gruppen[0].punkte[0] == 100
    assert result.gruppen[0].konflikt is True


def test_geprueft_wird_bei_abweichung_wieder_geoeffnet():
    existing = _gruppe("img1.jpg", 1, bogen_id="alt")
    existing.geprueft = True
    existing.recompute()

    incoming = _gruppe("img1.jpg", 1, bogen_id="neu")
    incoming.punkte[0] = 100
    incoming.recompute()

    result = merge_gruppen([existing], [incoming])
    assert result.gruppen[0].geprueft is False
    assert result.gruppen[0].konflikt is True


def test_identitaetskonflikt_wird_typisiert():
    existing = _gruppe("img1.jpg", 1, bogen_id="b1-p1")
    incoming = _gruppe("img1.jpg", 1, bogen_id="b1-p1")
    incoming.spieler_nr = "99"

    result = merge_gruppen([existing], [incoming])

    assert result.konflikte == 1
    assert existing.konflikt is True
    assert existing.konflikt_art == "identitaet"
    assert "identitaet_konflikt" in existing.statuses


def test_duplikat_mit_anderem_namen_markiert_name_konflikt():
    existing = _gruppe("img1.jpg", 1, bogen_id="alt")
    incoming = _gruppe("img1.jpg", 1, bogen_id="neu")
    incoming.spieler_name = "Anders"

    result = merge_gruppen([existing], [incoming])

    assert result.duplikate == 1
    assert "name_konflikt" in existing.statuses
    assert "Anders" in existing.warnung_text


def test_gleiche_spieler_nummer_auf_einem_bogen_bleibt_doppelt():
    a = _gruppe("img1.jpg", 1, bogen_id="b1", durchgang=1)
    b = _gruppe("img1.jpg", 1, bogen_id="b1", durchgang=1)
    b.position = 2

    result = merge_gruppen([], [a, b])

    assert result.neue_gruppen == 2
    assert len(result.gruppen) == 2
    assert "spieler_doppelt" in a.statuses
    assert "spieler_doppelt" in b.statuses


def test_platzhalter_wird_durch_lesbare_daten_ersetzt():
    placeholder = Gruppe(
        ref=BogenRef("b1-p1", "x", 1),
        position=0,
        durchgang_nr=1,
        spieler_nr="",
        spieler_name="",
        placeholder=True,
    )
    placeholder.recompute()
    incoming = _gruppe("img1.jpg", 1, bogen_id="b1-p1")
    result = merge_gruppen([placeholder], [incoming])
    assert result.neue_gruppen == 1
    assert len(result.gruppen) == 1
    assert result.gruppen[0].placeholder is False


def test_namenskonflikt_und_kanonischer_name():
    a = _gruppe("img1.jpg", 1, bogen_id="b1")
    b = _gruppe("img1.jpg", 1, bogen_id="b2")
    b.spieler_name = "Anders"
    apply_identity_checks([a, b])
    assert "name_konflikt" in a.statuses
    assert "name_konflikt" in b.statuses


def test_spieler_nummer_doppelt_auf_einem_bogen():
    a = _gruppe("img1.jpg", 1, bogen_id="b1", durchgang=1)
    b = _gruppe("img1.jpg", 1, bogen_id="b1", durchgang=2)
    b.durchgang_nr = 1
    apply_identity_checks([a, b])
    assert "spieler_doppelt" in a.statuses
    assert "spieler_doppelt" in b.statuses
