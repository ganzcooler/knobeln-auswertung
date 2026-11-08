"""Abbildung der LLM-Antwort auf die Domänenobjekte."""

from __future__ import annotations

from ..domain.models import BogenRef, Gruppe, NeueBogen
from ..domain.normalize import as_text, normalize_punkte, normalize_summe
from .models import BogenLLM, SpielerLLM, WurfZeileLLM


def gruppe_from_llm(
    *,
    ref: BogenRef,
    durchgang_nr: int | None,
    spieler: SpielerLLM,
    position: int,
) -> Gruppe:
    wurf_zeilen = _pad_wurf_zeilen(spieler.wurf_zeilen)
    punkte: list[int | None] = []
    roh: list[str] = []
    korrekturen: list[str | None] = []
    llm_hinweise: list[str | None] = []

    for wurf in wurf_zeilen:
        norm = normalize_punkte(wurf.roh, wurf.punkte)
        punkte.append(norm.punkte)
        roh.append(as_text(wurf.roh))
        korrekturen.append(norm.korrektur)
        llm_hinweise.append(as_text(wurf.hinweis) or None)

    summe = normalize_summe(
        spieler.summe_bogen.roh,
        spieler.summe_bogen.punkte,
    )

    gruppe = Gruppe(
        ref=ref,
        position=position,
        durchgang_nr=durchgang_nr,
        spieler_nr=as_text(spieler.spieler_nr),
        spieler_name=as_text(spieler.spieler_name),
        punkte=punkte,
        punkte_roh=roh,
        korrekturen=korrekturen,
        llm_hinweise=llm_hinweise,
        summe_bogen=summe.summe,
        summe_bogen_roh=as_text(spieler.summe_bogen.roh),
        summe_bogen_status=summe.status,
    )
    gruppe.recompute()
    return gruppe


def build_neue_bogen(
    response: BogenLLM,
    *,
    ref: BogenRef,
) -> NeueBogen:
    if response.bogen_unklar:
        return NeueBogen(
            ref=ref,
            durchgang_nr=response.durchgang_nr,
            spieler=[],
            bogen_unklar=True,
        )

    by_position = {p.position: p for p in response.spieler}
    gruppen: list[Gruppe] = []
    for position in range(1, 5):
        spieler = by_position.get(position)
        if spieler is None:
            spieler = SpielerLLM(position=position)
        gruppen.append(
            gruppe_from_llm(
                ref=ref,
                durchgang_nr=response.durchgang_nr,
                spieler=spieler,
                position=position,
            )
        )

    return NeueBogen(
        ref=ref,
        durchgang_nr=response.durchgang_nr,
        spieler=gruppen,
        bogen_unklar=False,
    )


def _pad_wurf_zeilen(
    wurf_zeilen: list[WurfZeileLLM],
) -> list[WurfZeileLLM]:
    by_nr: dict[int, WurfZeileLLM] = {}
    for wurf in wurf_zeilen:
        if 1 <= wurf.wurf_nr <= 12:
            by_nr[wurf.wurf_nr] = wurf
    return [
        by_nr.get(
            nr,
            WurfZeileLLM(wurf_nr=nr, roh="", punkte=None, hinweis=None),
        )
        for nr in range(1, 13)
    ]
