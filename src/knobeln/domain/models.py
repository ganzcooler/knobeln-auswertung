"""Domänenmodelle für eine Spielergruppe und einen Bogen."""

from __future__ import annotations

from dataclasses import dataclass, field

from .wertung import GUELTIGE_PUNKTE, ist_gueltige_summe

STATUS_ORDER = [
    "bogen_unklar",
    "durchgang_unklar",
    "spieler_unklar",
    "spieler_doppelt",
    "konflikt",
    "identitaet_konflikt",
    "summe_fehlt",
    "summe_ungueltig",
    "summe_unvollstaendig",
    "summe_abweichung",
    "summe_korrigiert",
    "wert_fehlt",
    "wert_ungueltig",
    "wert_korrigiert",
    "name_konflikt",
    "geprueft",
    "ok",
]
_STATUS_RANK = {code: i for i, code in enumerate(STATUS_ORDER)}


def _status_sort_key(code: str) -> tuple[int, str]:
    return (_STATUS_RANK.get(code, len(STATUS_ORDER)), code)


@dataclass(frozen=True)
class BogenRef:
    bogen_id: str
    quelle: str
    seite: int


@dataclass
class Gruppe:
    ref: BogenRef
    position: int
    durchgang_nr: int | None
    spieler_nr: str
    spieler_name: str
    punkte: list[int | None] = field(default_factory=lambda: [None] * 12)
    punkte_roh: list[str] = field(default_factory=lambda: [""] * 12)
    korrekturen: list[str | None] = field(default_factory=lambda: [None] * 12)
    llm_hinweise: list[str | None] = field(default_factory=lambda: [None] * 12)
    summe_bogen: int | None = None
    summe_bogen_roh: str = ""
    summe_bogen_status: str | None = None
    konflikt: bool = False
    konflikt_art: str = ""  # "daten" | "identitaet"
    konflikt_detail: str = ""
    geprueft: bool = False
    kommentare: list[str] = field(default_factory=lambda: [""] * 12)
    name_conflict_names: set[str] = field(default_factory=set)
    extra_by_wurf: dict[int | None, dict[str, str]] = field(default_factory=dict)
    placeholder: bool = False
    zusatz_status: set[str] = field(default_factory=set)
    zusatz_warnungen: list[str] = field(default_factory=list)
    summe_berechnet: int | None = None
    delta: int | None = None
    statuses: set[str] = field(default_factory=set)
    warnungen: list[str] = field(default_factory=list)

    # -- Ableitungen ------------------------------------------------------

    @property
    def bogen_id(self) -> str:
        return self.ref.bogen_id

    @property
    def quelle(self) -> str:
        return self.ref.quelle

    @property
    def seite(self) -> int:
        return self.ref.seite

    @property
    def status_text(self) -> str:
        if not self.statuses:
            return "ok"
        return "|".join(sorted(self.statuses, key=_status_sort_key))

    @property
    def warnung_text(self) -> str:
        seen: list[str] = []
        for warning in self.warnungen:
            if warning not in seen:
                seen.append(warning)
        return "; ".join(seen)

    def player_key(self) -> tuple[int, str] | None:
        if self.durchgang_nr is None or not self.spieler_nr:
            return None
        return (self.durchgang_nr, self.spieler_nr)

    def bogen_position_key(self) -> tuple[str, int]:
        return (self.bogen_id, self.position)

    def ist_offen(self) -> bool:
        if self.placeholder:
            return True
        if self.geprueft:
            return False
        return bool(self.statuses - {"ok", "geprueft"})

    def clear_extras(self) -> None:
        self.zusatz_status.clear()
        self.zusatz_warnungen.clear()

    def recompute(self) -> None:
        self.statuses = set(self.zusatz_status)
        warnungen: list[str] = list(self.zusatz_warnungen)

        if self.placeholder:
            self.summe_berechnet = None
            self.delta = None
            self.statuses = {"bogen_unklar"}
            self.warnungen = ["Bogen konnte nicht gelesen werden."]
            self.warnungen.extend(self.zusatz_warnungen)
            return

        if self.durchgang_nr is None or not 1 <= self.durchgang_nr <= 5:
            self.statuses.add("durchgang_unklar")
            warnungen.append("Durchgang-Nr. fehlt oder liegt außerhalb 1–5.")

        if not self.spieler_nr:
            self.statuses.add("spieler_unklar")
            warnungen.append("Spieler-Nr. fehlt.")

        fehlend: list[int] = []
        ungueltig: list[int] = []
        korrigiert: list[int] = []

        for i, wert in enumerate(self.punkte):
            if wert is None:
                if not self.punkte_roh[i].strip():
                    self.statuses.add("wert_fehlt")
                    fehlend.append(i + 1)
                else:
                    self.statuses.add("wert_ungueltig")
                    ungueltig.append(i + 1)
            elif wert not in GUELTIGE_PUNKTE:
                self.statuses.add("wert_ungueltig")
                ungueltig.append(i + 1)

            if self.korrekturen[i] and wert is not None:
                self.statuses.add("wert_korrigiert")
                korrigiert.append(i + 1)

        if fehlend:
            warnungen.append(f"Fehlende Werte in Wurf {_wurf_liste(fehlend)}.")
        if ungueltig:
            details = ", ".join(
                f"Wurf {i}: {self.punkte_roh[i - 1] or 'leer'}" for i in ungueltig
            )
            warnungen.append(f"Ungültige Werte ({details}).")
        for i in korrigiert:
            note = self.korrekturen[i - 1]
            if note:
                warnungen.append(f"Wurf {i}: {note}.")

        for i, hint in enumerate(self.llm_hinweise, start=1):
            if hint:
                warnungen.append(f"LLM-Hinweis Wurf {i}: {hint}.")

        self.summe_berechnet = (
            sum(w for w in self.punkte if w is not None)
            if all(w is not None and w in GUELTIGE_PUNKTE for w in self.punkte)
            else None
        )

        if self.summe_bogen is None:
            if self.summe_bogen_status == "summe_ungueltig":
                self.statuses.add("summe_ungueltig")
                warnungen.append("Summenzeile ist ungültig (0–2400, durch 5 teilbar).")
            else:
                self.statuses.add("summe_fehlt")
                warnungen.append("Summenzeile fehlt.")
        elif not ist_gueltige_summe(self.summe_bogen):
            self.statuses.add("summe_ungueltig")
            warnungen.append("Summenzeile ist ungültig (0–2400, durch 5 teilbar).")
        elif self.summe_bogen_status == "summe_korrigiert":
            self.statuses.add("summe_korrigiert")
            if self.summe_bogen_roh:
                warnungen.append(
                    f"Summe korrigiert: {self.summe_bogen_roh} -> {self.summe_bogen}."
                )

        if self.summe_berechnet is None:
            if self.summe_bogen is not None:
                self.statuses.add("summe_unvollstaendig")
                warnungen.append(
                    "Berechnete Summe unvollständig, weil Zellwerte fehlen."
                )
            self.delta = None
        elif self.summe_bogen is not None and ist_gueltige_summe(self.summe_bogen):
            self.delta = self.summe_bogen - self.summe_berechnet
            if self.delta != 0:
                self.statuses.add("summe_abweichung")
                warnungen.append(
                    "Summe laut Bogen "
                    f"{self.summe_bogen}, berechnet {self.summe_berechnet} "
                    f"(Delta {self.delta:+d})."
                )
        else:
            self.delta = None

        if self.konflikt:
            code = (
                "identitaet_konflikt"
                if self.konflikt_art == "identitaet"
                else "konflikt"
            )
            self.statuses.add(code)
            detail = self.konflikt_detail or "abweichende Werte"
            warnungen.append(f"Konflikt: {detail}. Bestehende Werte unverändert.")

        if self.geprueft and self.statuses:
            self.statuses.add("geprueft")
            warnungen.append("Vom Menschen geprüft.")

        if not self.statuses:
            self.statuses.add("ok")

        self.warnungen = warnungen


@dataclass
class NeueBogen:
    ref: BogenRef
    durchgang_nr: int | None
    spieler: list[Gruppe] = field(default_factory=list)
    bogen_unklar: bool = False


def _wurf_liste(numbers: list[int]) -> str:
    return ", ".join(str(n) for n in numbers)
