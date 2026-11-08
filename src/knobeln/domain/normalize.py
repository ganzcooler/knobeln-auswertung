"""Zell- und Summen-Normalisierung.

Grundsatz: Die Wertungstabelle ist maßgeblich. Nur eindeutige
Trennzeichen-Artefakte (8.5 -> 85) werden korrigiert; es wird nie gerundet
oder auf einen Bereich geklemmt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .wertung import GUELTIGE_PUNKTE, ist_gueltige_summe

_SEPARATOR_RE = re.compile(r"[.,\s']")
_DIGITS_RE = re.compile(r"^\d+$")
_SLASHES = {"/", "\\"}


@dataclass(frozen=True)
class NormalizedPunkte:
    punkte: int | None
    korrektur: str | None
    status: str | None


@dataclass(frozen=True)
class NormalizedSumme:
    summe: int | None
    korrektur: str | None
    status: str | None


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'")


def _candidate_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None
    if isinstance(value, str):
        text = value.strip()
        if _DIGITS_RE.fullmatch(text):
            return int(text)
    return None


def clean_separators(raw: str) -> str:
    """Entfernt nur Trennzeichen; Buchstaben bleiben stehen."""
    return _SEPARATOR_RE.sub("", raw)


def _cleaned_candidate(raw: str, valid) -> int | None:
    cleaned = clean_separators(raw)
    if not cleaned or cleaned == raw or not _DIGITS_RE.fullmatch(cleaned):
        return None
    value = int(cleaned)
    return value if valid(value) else None


def _is_zero_text(raw: str) -> bool:
    """Erkennt 0, 0.0, 0,0, 00 usw. als geschriebene Null."""
    cleaned = clean_separators(raw)
    return bool(cleaned) and set(cleaned) == {"0"}


def _normalize_value(
    raw: object,
    candidate: object,
    *,
    valid,
    missing_status: str,
    invalid_status: str,
    corrected_status: str,
) -> tuple[int | None, str | None, str | None]:
    raw_text = _text(raw)
    cand = _candidate_int(candidate)

    if not raw_text:
        return None, None, missing_status

    if raw_text in _SLASHES:
        return 0, None, None

    if _is_zero_text(raw_text):
        if cand is not None and cand != 0:
            return 0, f"{raw_text} -> 0 (LLM: {cand})", corrected_status
        if raw_text != "0":
            return (
                0,
                f"{raw_text} -> 0 (Trennzeichen entfernt)",
                corrected_status,
            )
        return 0, None, None

    cleaned = _cleaned_candidate(raw_text, valid)
    if cleaned is not None:
        if cand is not None and valid(cand) and cand != cleaned:
            note = f"{raw_text} -> {cleaned} (Trennzeichen; LLM: {cand})"
        else:
            note = f"{raw_text} -> {cleaned} (Trennzeichen entfernt)"
        return cleaned, note, corrected_status

    if cand is not None and valid(cand):
        if raw_text != str(cand):
            return cand, f"{raw_text} -> {cand} (LLM)", corrected_status
        return cand, None, None

    return None, None, invalid_status


def normalize_punkte(raw: object, candidate: object = None) -> NormalizedPunkte:
    punkte, korrektur, status = _normalize_value(
        raw,
        candidate,
        valid=lambda value: value in GUELTIGE_PUNKTE,
        missing_status="wert_fehlt",
        invalid_status="wert_ungueltig",
        corrected_status="wert_korrigiert",
    )
    return NormalizedPunkte(punkte, korrektur, status)


def normalize_summe(raw: object, candidate: object = None) -> NormalizedSumme:
    summe, korrektur, status = _normalize_value(
        raw,
        candidate,
        valid=ist_gueltige_summe,
        missing_status="summe_fehlt",
        invalid_status="summe_ungueltig",
        corrected_status="summe_korrigiert",
    )
    return NormalizedSumme(summe, korrektur, status)


def parse_int(value: object) -> int | None:
    """Liest einen optionalen Integer aus der CSV, ohne Sonderregeln."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
