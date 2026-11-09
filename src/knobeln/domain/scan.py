"""Domänenmodelle für Durchgänge, Bögen und gespeicherte Spielergruppen."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Gruppe


@dataclass(frozen=True)
class Durchgang:
    id: int
    turnier_id: int
    nummer: int
    status: str


@dataclass(frozen=True)
class Bogen:
    id: int
    durchgang_id: int
    dateiname: str
    archiv_pfad: str
    seite: int
    bogen_id: str
    status: str
    job_status: str = "warten"
    job_prompt_tokens: int = 0
    job_completion_tokens: int = 0
    job_cost_usd: float = 0.0


@dataclass(frozen=True)
class Job:
    id: int
    bogen_id: int
    status: str
    fehler: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass
class StoredGruppe:
    id: int
    durchgang_id: int
    bogen_id: int | None
    gruppe: Gruppe
    quelle: str
    ergebnis_status: str
    konflikt_id: int | None


@dataclass(frozen=True)
class Konflikt:
    id: int
    durchgang_id: int
    spieler_nr: str
    gruppe_a_id: int
    gruppe_b_id: int
    status: str
    gewaehlt_gruppe_id: int | None
