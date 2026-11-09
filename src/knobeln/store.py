"""SQLite-Persistenz für Turniere und Anwendungszustand."""

from __future__ import annotations

import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .domain.turnier import Turnier


class SQLiteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS turnier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def create_turnier(self, name: str) -> Turnier:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO turnier (name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now),
            )
            turnier_id = int(cursor.lastrowid or 0)
        return Turnier(id=turnier_id, name=name)

    def list_turniere(self) -> list[Turnier]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name FROM turnier ORDER BY id"
            ).fetchall()
        return [Turnier(id=int(row["id"]), name=str(row["name"])) for row in rows]

    def get_turnier(self, turnier_id: int) -> Turnier | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name FROM turnier WHERE id = ?", (turnier_id,)
            ).fetchone()
        if row is None:
            return None
        return Turnier(id=int(row["id"]), name=str(row["name"]))

    def rename_turnier(self, turnier_id: int, name: str) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                "UPDATE turnier SET name = ?, updated_at = ? WHERE id = ?",
                (name, now, turnier_id),
            )

    def delete_turnier(self, turnier_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM turnier WHERE id = ?", (turnier_id,))

    def set_last_opened(self, turnier_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_state (key, value) VALUES ('last_opened_turnier', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(turnier_id),),
            )

    def get_last_opened_id(self) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = 'last_opened_turnier'"
            ).fetchone()
        if row is None:
            return None
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            return None

    def clear_last_opened(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM app_state WHERE key = 'last_opened_turnier'"
            )

    def backup(self) -> Path:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        destination = self.path.with_name(f"{self.path.name}.{stamp}.bak")
        shutil.copy2(self.path, destination)
        return destination
