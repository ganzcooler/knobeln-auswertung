"""Pydantic-Modelle für die strukturierte LLM-Antwort."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WurfZeileLLM(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wurf_nr: int = Field(ge=1, le=12)
    roh: str = ""
    punkte: float | int | None = None
    hinweis: str | None = None


class SummeLLM(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roh: str = ""
    punkte: float | int | None = None
    hinweis: str | None = None


class SpielerLLM(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: int = Field(ge=1, le=4)
    spieler_nr: str | None = None
    spieler_name: str | None = None
    wurf_zeilen: list[WurfZeileLLM] = Field(default_factory=list)
    summe_bogen: SummeLLM = Field(default_factory=SummeLLM)

    @model_validator(mode="after")
    def _validate_wurf_zeilen(self) -> "SpielerLLM":
        if not self.wurf_zeilen:
            return self
        if len(self.wurf_zeilen) != 12:
            raise ValueError(
                "wurf_zeilen muss entweder leer oder genau zwölf Einträge "
                "enthalten"
            )
        nummern = sorted(w.wurf_nr for w in self.wurf_zeilen)
        if nummern != list(range(1, 13)):
            raise ValueError(
                "wurf_zeilen muss Wurf-Nr. 1–12 genau einmal enthalten"
            )
        return self


class BogenLLM(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bogen_unklar: bool = False
    hinweis: str | None = None
    durchgang_nr: int | None = None
    spieler: list[SpielerLLM] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_spieler(self) -> "BogenLLM":
        if not self.spieler:
            if self.bogen_unklar:
                return self
            raise ValueError(
                "spieler muss bei einem lesbaren Bogen vier Einträge enthalten"
            )
        if len(self.spieler) != 4:
            raise ValueError(
                "spieler muss entweder leer (bogen_unklar) oder genau vier "
                "Einträge enthalten"
            )
        positionen = sorted(p.position for p in self.spieler)
        if positionen != [1, 2, 3, 4]:
            raise ValueError(
                "spieler muss die Positionen 1–4 genau einmal enthalten"
            )
        return self
