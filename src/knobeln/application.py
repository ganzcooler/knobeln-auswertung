"""Anwendungskern für Turniere und die gemeinsame Web-/CLI-Nutzung."""

from __future__ import annotations

from .domain.turnier import Turnier
from .store import SQLiteStore


class KnobelnService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def create_turnier(self, name: str) -> Turnier:
        clean_name = self._require_name(name)
        turnier = self.store.create_turnier(clean_name)
        self.store.set_last_opened(turnier.id)
        return turnier

    def list_turniere(self) -> list[Turnier]:
        return self.store.list_turniere()

    def get_turnier(self, turnier_id: int) -> Turnier:
        turnier = self.store.get_turnier(turnier_id)
        if turnier is None:
            raise LookupError(f"Turnier {turnier_id} nicht gefunden.")
        return turnier

    def rename_turnier(self, turnier_id: int, name: str) -> Turnier:
        self.get_turnier(turnier_id)
        clean_name = self._require_name(name)
        self.store.rename_turnier(turnier_id, clean_name)
        return Turnier(id=turnier_id, name=clean_name)

    def open_turnier(self, turnier_id: int) -> Turnier:
        turnier = self.get_turnier(turnier_id)
        self.store.set_last_opened(turnier_id)
        return turnier

    def last_opened_turnier(self) -> Turnier | None:
        turnier_id = self.store.get_last_opened_id()
        if turnier_id is None:
            return None
        return self.store.get_turnier(turnier_id)

    def delete_turnier(self, turnier_id: int) -> None:
        self.get_turnier(turnier_id)
        self.store.backup()
        self.store.delete_turnier(turnier_id)
        if self.store.get_last_opened_id() == turnier_id:
            self.store.clear_last_opened()

    @staticmethod
    def _require_name(name: str) -> str:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Der Turniername darf nicht leer sein.")
        return clean_name
