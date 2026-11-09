"""Domänenmodell für ein Turnier."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Turnier:
    id: int
    name: str
