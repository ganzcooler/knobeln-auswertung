"""SQLite-Persistenz für Turniere, Durchgänge, Bögen und Ergebnisse."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .domain.models import BogenRef, Gruppe
from .domain.scan import Bogen, Durchgang, Job, Konflikt, StoredGruppe
from .domain.turnier import Turnier


class SQLiteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS turnier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS durchgang (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turnier_id INTEGER NOT NULL REFERENCES turnier(id) ON DELETE CASCADE,
                    nummer INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'offen',
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    UNIQUE(turnier_id, nummer)
                );

                CREATE TABLE IF NOT EXISTS bogen (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    durchgang_id INTEGER NOT NULL REFERENCES durchgang(id) ON DELETE CASCADE,
                    dateiname TEXT NOT NULL,
                    archiv_pfad TEXT NOT NULL,
                    seite INTEGER NOT NULL,
                    bogen_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'warten',
                    created_at TEXT NOT NULL,
                    UNIQUE(durchgang_id, bogen_id)
                );

                CREATE TABLE IF NOT EXISTS job (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bogen_id INTEGER NOT NULL UNIQUE REFERENCES bogen(id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'warten',
                    fehler TEXT NOT NULL DEFAULT '',
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0,
                    cost_usd REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gruppe (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    durchgang_id INTEGER NOT NULL REFERENCES durchgang(id) ON DELETE CASCADE,
                    bogen_id INTEGER REFERENCES bogen(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL,
                    spieler_nr TEXT NOT NULL DEFAULT '',
                    spieler_name TEXT NOT NULL DEFAULT '',
                    quelle TEXT NOT NULL DEFAULT 'scan',
                    punkte_json TEXT NOT NULL,
                    punkte_roh_json TEXT NOT NULL,
                    korrekturen_json TEXT NOT NULL,
                    hinweise_json TEXT NOT NULL,
                    summe_bogen INTEGER,
                    summe_bogen_roh TEXT NOT NULL DEFAULT '',
                    summe_bogen_status TEXT NOT NULL DEFAULT '',
                    statuses TEXT NOT NULL DEFAULT '',
                    warnungen_json TEXT NOT NULL DEFAULT '[]',
                    kommentare_json TEXT NOT NULL DEFAULT '[]',
                    konflikt INTEGER NOT NULL DEFAULT 0,
                    konflikt_art TEXT NOT NULL DEFAULT '',
                    konflikt_detail TEXT NOT NULL DEFAULT '',
                    geprueft INTEGER NOT NULL DEFAULT 0,
                    ergebnis_status TEXT NOT NULL DEFAULT 'aktiv',
                    konflikt_id INTEGER,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS konflikt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    durchgang_id INTEGER NOT NULL REFERENCES durchgang(id) ON DELETE CASCADE,
                    spieler_nr TEXT NOT NULL,
                    gruppe_a_id INTEGER NOT NULL REFERENCES gruppe(id),
                    gruppe_b_id INTEGER NOT NULL REFERENCES gruppe(id),
                    status TEXT NOT NULL DEFAULT 'offen',
                    gewaehlt_gruppe_id INTEGER REFERENCES gruppe(id),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(gruppe)")
            }
            if "kommentare_json" not in columns:
                connection.execute(
                    "ALTER TABLE gruppe ADD COLUMN kommentare_json TEXT NOT NULL DEFAULT '[]'"
                )

    # -- Turnier ---------------------------------------------------------

    def create_turnier(self, name: str) -> Turnier:
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO turnier (name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite hat keine Turnier-ID vergeben.")
            turnier_id = int(cursor.lastrowid)
        return Turnier(id=turnier_id, name=name)

    def list_turniere(self) -> list[Turnier]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name FROM turnier ORDER BY id"
            ).fetchall()
        return [self._turnier_from_row(row) for row in rows]

    def get_turnier(self, turnier_id: int) -> Turnier | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name FROM turnier WHERE id = ?", (turnier_id,)
            ).fetchone()
        if row is None:
            return None
        return self._turnier_from_row(row)

    def rename_turnier(self, turnier_id: int, name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE turnier SET name = ?, updated_at = ? WHERE id = ?",
                (name, _now(), turnier_id),
            )

    def delete_turnier(self, turnier_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM turnier WHERE id = ?", (turnier_id,))

    @staticmethod
    def _turnier_from_row(row: sqlite3.Row) -> Turnier:
        return Turnier(id=int(row["id"]), name=str(row["name"]))

    # -- Durchgang -------------------------------------------------------

    def create_durchgang(self, turnier_id: int, nummer: int) -> Durchgang:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO durchgang (turnier_id, nummer, created_at) VALUES (?, ?, ?)",
                (turnier_id, nummer, _now()),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite hat keine Durchgang-ID vergeben.")
            durchgang_id = int(cursor.lastrowid)
        return Durchgang(
            id=durchgang_id,
            turnier_id=turnier_id,
            nummer=nummer,
            status="offen",
        )

    def list_durchgaenge(self, turnier_id: int) -> list[Durchgang]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, turnier_id, nummer, status
                FROM durchgang WHERE turnier_id = ? ORDER BY nummer
                """,
                (turnier_id,),
            ).fetchall()
        return [self._durchgang_from_row(row) for row in rows]

    def get_durchgang(self, durchgang_id: int) -> Durchgang | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, turnier_id, nummer, status
                FROM durchgang WHERE id = ?
                """,
                (durchgang_id,),
            ).fetchone()
        if row is None:
            return None
        return self._durchgang_from_row(row)

    def get_durchgang_by_nummer(self, turnier_id: int, nummer: int) -> Durchgang | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, turnier_id, nummer, status
                FROM durchgang WHERE turnier_id = ? AND nummer = ?
                """,
                (turnier_id, nummer),
            ).fetchone()
        if row is None:
            return None
        return self._durchgang_from_row(row)

    def set_durchgang_status(self, durchgang_id: int, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE durchgang
                SET status = ?, closed_at = CASE WHEN ? = 'abgeschlossen' THEN ? ELSE NULL END
                WHERE id = ?
                """,
                (status, status, _now(), durchgang_id),
            )

    @staticmethod
    def _durchgang_from_row(row: sqlite3.Row) -> Durchgang:
        return Durchgang(
            id=int(row["id"]),
            turnier_id=int(row["turnier_id"]),
            nummer=int(row["nummer"]),
            status=str(row["status"]),
        )

    # -- Bogen und Job ---------------------------------------------------

    def create_bogen(
        self,
        *,
        durchgang_id: int,
        dateiname: str,
        archiv_pfad: str,
        seite: int,
        bogen_id: str,
    ) -> Bogen:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO bogen
                    (durchgang_id, dateiname, archiv_pfad, seite, bogen_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (durchgang_id, dateiname, archiv_pfad, seite, bogen_id, _now()),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite hat keine Bogen-ID vergeben.")
            bogen_pk = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO job (bogen_id, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                (bogen_pk, _now(), _now()),
            )
        return Bogen(
            id=bogen_pk,
            durchgang_id=durchgang_id,
            dateiname=dateiname,
            archiv_pfad=archiv_pfad,
            seite=seite,
            bogen_id=bogen_id,
            status="warten",
        )

    def list_bogen(self, durchgang_id: int) -> list[Bogen]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT b.*, COALESCE(j.status, 'warten') AS job_status,
                       COALESCE(j.prompt_tokens, 0) AS job_prompt_tokens,
                       COALESCE(j.completion_tokens, 0) AS job_completion_tokens,
                       COALESCE(j.cost_usd, 0) AS job_cost_usd
                FROM bogen b LEFT JOIN job j ON j.bogen_id = b.id
                WHERE b.durchgang_id = ? ORDER BY b.id
                """,
                (durchgang_id,),
            ).fetchall()
        return [self._bogen_from_row(row) for row in rows]

    def get_bogen(self, bogen_id: int) -> Bogen | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT b.*, COALESCE(j.status, 'warten') AS job_status,
                       COALESCE(j.prompt_tokens, 0) AS job_prompt_tokens,
                       COALESCE(j.completion_tokens, 0) AS job_completion_tokens,
                       COALESCE(j.cost_usd, 0) AS job_cost_usd
                FROM bogen b LEFT JOIN job j ON j.bogen_id = b.id
                WHERE b.id = ?
                """,
                (bogen_id,),
            ).fetchone()
        if row is None:
            return None
        return self._bogen_from_row(row)

    def find_bogen_by_bogen_id(self, durchgang_id: int, bogen_id: str) -> Bogen | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT b.*, COALESCE(j.status, 'warten') AS job_status,
                       COALESCE(j.prompt_tokens, 0) AS job_prompt_tokens,
                       COALESCE(j.completion_tokens, 0) AS job_completion_tokens,
                       COALESCE(j.cost_usd, 0) AS job_cost_usd
                FROM bogen b LEFT JOIN job j ON j.bogen_id = b.id
                WHERE b.durchgang_id = ? AND b.bogen_id = ?
                """,
                (durchgang_id, bogen_id),
            ).fetchone()
        if row is None:
            return None
        return self._bogen_from_row(row)

    def set_bogen_status(self, bogen_id: int, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE bogen SET status = ? WHERE id = ?", (status, bogen_id)
            )

    @staticmethod
    def _bogen_from_row(row: sqlite3.Row) -> Bogen:
        return Bogen(
            id=int(row["id"]),
            durchgang_id=int(row["durchgang_id"]),
            dateiname=str(row["dateiname"]),
            archiv_pfad=str(row["archiv_pfad"]),
            seite=int(row["seite"]),
            bogen_id=str(row["bogen_id"]),
            status=str(row["status"]),
            job_status=str(row["job_status"]),
            job_prompt_tokens=int(row["job_prompt_tokens"]),
            job_completion_tokens=int(row["job_completion_tokens"]),
            job_cost_usd=float(row["job_cost_usd"]),
        )

    def get_job(self, bogen_id: int) -> Job | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM job WHERE bogen_id = ?", (bogen_id,)
            ).fetchone()
        if row is None:
            return None
        return self._job_from_row(row)

    def list_pending_jobs(self) -> list[Job]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM job WHERE status = 'warten' ORDER BY id"
            ).fetchall()
        return [self._job_from_row(row) for row in rows]

    def update_job(
        self,
        bogen_id: int,
        *,
        status: str,
        fehler: str = "",
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        cost_usd: float | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE job SET
                    status = ?,
                    fehler = ?,
                    prompt_tokens = COALESCE(?, prompt_tokens),
                    completion_tokens = COALESCE(?, completion_tokens),
                    cost_usd = COALESCE(?, cost_usd),
                    updated_at = ?
                WHERE bogen_id = ?
                """,
                (
                    status,
                    fehler,
                    prompt_tokens,
                    completion_tokens,
                    cost_usd,
                    _now(),
                    bogen_id,
                ),
            )

    def retry_job(self, bogen_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE job SET status = 'warten', fehler = '', updated_at = ?
                WHERE bogen_id = ?
                """,
                (_now(), bogen_id),
            )
            connection.execute(
                "UPDATE bogen SET status = 'warten' WHERE id = ?", (bogen_id,)
            )

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> Job:
        return Job(
            id=int(row["id"]),
            bogen_id=int(row["bogen_id"]),
            status=str(row["status"]),
            fehler=str(row["fehler"]),
            prompt_tokens=int(row["prompt_tokens"]),
            completion_tokens=int(row["completion_tokens"]),
            cost_usd=float(row["cost_usd"]),
        )

    # -- Gruppen ---------------------------------------------------------

    def save_gruppe(
        self,
        *,
        durchgang_id: int,
        bogen_id: int | None,
        gruppe: Gruppe,
        quelle: str,
        ergebnis_status: str = "aktiv",
        konflikt_id: int | None = None,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO gruppe (
                    durchgang_id, bogen_id, position, spieler_nr, spieler_name,
                    quelle, punkte_json, punkte_roh_json, korrekturen_json,
                    hinweise_json, summe_bogen, summe_bogen_roh,
                    summe_bogen_status, statuses, warnungen_json,
                    kommentare_json, konflikt, konflikt_art, konflikt_detail,
                    geprueft, ergebnis_status, konflikt_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._gruppe_values(
                    durchgang_id=durchgang_id,
                    bogen_id=bogen_id,
                    gruppe=gruppe,
                    quelle=quelle,
                    ergebnis_status=ergebnis_status,
                    konflikt_id=konflikt_id,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite hat keine Gruppen-ID vergeben.")
            return int(cursor.lastrowid)

    def update_gruppe(self, stored: StoredGruppe) -> None:
        gruppe = stored.gruppe
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE gruppe SET
                    position = ?, spieler_nr = ?, spieler_name = ?, quelle = ?,
                    punkte_json = ?, punkte_roh_json = ?, korrekturen_json = ?,
                    hinweise_json = ?, summe_bogen = ?, summe_bogen_roh = ?,
                    summe_bogen_status = ?, statuses = ?, warnungen_json = ?,
                    kommentare_json = ?, konflikt = ?, konflikt_art = ?,
                    konflikt_detail = ?, geprueft = ?, ergebnis_status = ?,
                    konflikt_id = ?
                WHERE id = ?
                """,
                (
                    gruppe.position,
                    gruppe.spieler_nr,
                    gruppe.spieler_name,
                    stored.quelle,
                    _json(gruppe.punkte),
                    _json(gruppe.punkte_roh),
                    _json(gruppe.korrekturen),
                    _json(gruppe.llm_hinweise),
                    gruppe.summe_bogen,
                    gruppe.summe_bogen_roh,
                    gruppe.summe_bogen_status or "",
                    "|".join(sorted(gruppe.statuses)),
                    _json(gruppe.warnungen),
                    _json(gruppe.kommentare),
                    1 if gruppe.konflikt else 0,
                    gruppe.konflikt_art,
                    gruppe.konflikt_detail,
                    1 if gruppe.geprueft else 0,
                    stored.ergebnis_status,
                    stored.konflikt_id,
                    stored.id,
                ),
            )

    def list_gruppen(self, durchgang_id: int) -> list[StoredGruppe]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT g.*, d.nummer AS durchgang_nummer,
                       b.bogen_id AS bogen_ref, b.dateiname AS bogen_dateiname,
                       b.seite AS bogen_seite
                FROM gruppe g
                JOIN durchgang d ON d.id = g.durchgang_id
                LEFT JOIN bogen b ON b.id = g.bogen_id
                WHERE g.durchgang_id = ?
                ORDER BY g.id
                """,
                (durchgang_id,),
            ).fetchall()
        return [self._stored_gruppe_from_row(row) for row in rows]

    def list_gruppen_for_bogen(self, bogen_id: int) -> list[StoredGruppe]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT g.*, d.nummer AS durchgang_nummer,
                       b.bogen_id AS bogen_ref, b.dateiname AS bogen_dateiname,
                       b.seite AS bogen_seite
                FROM gruppe g
                JOIN durchgang d ON d.id = g.durchgang_id
                LEFT JOIN bogen b ON b.id = g.bogen_id
                WHERE g.bogen_id = ?
                ORDER BY g.position
                """,
                (bogen_id,),
            ).fetchall()
        return [self._stored_gruppe_from_row(row) for row in rows]

    def list_gruppen_for_turnier(self, turnier_id: int) -> list[StoredGruppe]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT g.*, d.nummer AS durchgang_nummer,
                       b.bogen_id AS bogen_ref, b.dateiname AS bogen_dateiname,
                       b.seite AS bogen_seite
                FROM gruppe g
                JOIN durchgang d ON d.id = g.durchgang_id
                LEFT JOIN bogen b ON b.id = g.bogen_id
                WHERE d.turnier_id = ?
                ORDER BY d.nummer, g.id
                """,
                (turnier_id,),
            ).fetchall()
        return [self._stored_gruppe_from_row(row) for row in rows]

    def get_gruppe(self, gruppe_id: int) -> StoredGruppe | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT g.*, d.nummer AS durchgang_nummer,
                       b.bogen_id AS bogen_ref, b.dateiname AS bogen_dateiname,
                       b.seite AS bogen_seite
                FROM gruppe g
                JOIN durchgang d ON d.id = g.durchgang_id
                LEFT JOIN bogen b ON b.id = g.bogen_id
                WHERE g.id = ?
                """,
                (gruppe_id,),
            ).fetchone()
        if row is None:
            return None
        return self._stored_gruppe_from_row(row)

    def find_gruppen_for_player(
        self, durchgang_id: int, spieler_nr: str
    ) -> list[StoredGruppe]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT g.*, d.nummer AS durchgang_nummer,
                       b.bogen_id AS bogen_ref, b.dateiname AS bogen_dateiname,
                       b.seite AS bogen_seite
                FROM gruppe g
                JOIN durchgang d ON d.id = g.durchgang_id
                LEFT JOIN bogen b ON b.id = g.bogen_id
                WHERE g.durchgang_id = ? AND g.spieler_nr = ?
                ORDER BY g.id
                """,
                (durchgang_id, spieler_nr),
            ).fetchall()
        return [self._stored_gruppe_from_row(row) for row in rows]

    def delete_groups_for_bogen(self, bogen_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM konflikt
                WHERE gruppe_a_id IN (SELECT id FROM gruppe WHERE bogen_id = ?)
                   OR gruppe_b_id IN (SELECT id FROM gruppe WHERE bogen_id = ?)
                """,
                (bogen_id, bogen_id),
            )
            connection.execute("DELETE FROM gruppe WHERE bogen_id = ?", (bogen_id,))

    def set_gruppe_ergebnis_status(
        self,
        gruppe_id: int,
        status: str,
        *,
        konflikt_id: int | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE gruppe SET ergebnis_status = ?, konflikt_id = ?
                WHERE id = ?
                """,
                (status, konflikt_id, gruppe_id),
            )

    @staticmethod
    def _gruppe_values(
        *,
        durchgang_id: int,
        bogen_id: int | None,
        gruppe: Gruppe,
        quelle: str,
        ergebnis_status: str,
        konflikt_id: int | None,
    ) -> tuple[object, ...]:
        return (
            durchgang_id,
            bogen_id,
            gruppe.position,
            gruppe.spieler_nr,
            gruppe.spieler_name,
            quelle,
            _json(gruppe.punkte),
            _json(gruppe.punkte_roh),
            _json(gruppe.korrekturen),
            _json(gruppe.llm_hinweise),
            gruppe.summe_bogen,
            gruppe.summe_bogen_roh,
            gruppe.summe_bogen_status or "",
            "|".join(sorted(gruppe.statuses)),
            _json(gruppe.warnungen),
            _json(gruppe.kommentare),
            1 if gruppe.konflikt else 0,
            gruppe.konflikt_art,
            gruppe.konflikt_detail,
            1 if gruppe.geprueft else 0,
            ergebnis_status,
            konflikt_id,
            _now(),
        )

    @staticmethod
    def _stored_gruppe_from_row(row: sqlite3.Row) -> StoredGruppe:
        bogen_ref = str(row["bogen_ref"] or "")
        quelle = str(row["bogen_dateiname"] or "manuell")
        gruppe = Gruppe(
            ref=BogenRef(
                bogen_id=bogen_ref,
                quelle=quelle,
                seite=int(row["bogen_seite"] or 1),
            ),
            position=int(row["position"]),
            durchgang_nr=int(row["durchgang_nummer"]),
            spieler_nr=str(row["spieler_nr"]),
            spieler_name=str(row["spieler_name"]),
            punkte=[
                _int_or_none(value) for value in _load_json(row["punkte_json"], [])
            ],
            punkte_roh=[str(value) for value in _load_json(row["punkte_roh_json"], [])],
            korrekturen=[
                None if value is None else str(value)
                for value in _load_json(row["korrekturen_json"], [])
            ],
            llm_hinweise=[
                None if value is None else str(value)
                for value in _load_json(row["hinweise_json"], [])
            ],
            summe_bogen=_int_or_none(row["summe_bogen"]),
            summe_bogen_roh=str(row["summe_bogen_roh"]),
            summe_bogen_status=str(row["summe_bogen_status"]) or None,
            konflikt=bool(row["konflikt"]),
            konflikt_art=str(row["konflikt_art"]),
            konflikt_detail=str(row["konflikt_detail"]),
            geprueft=bool(row["geprueft"]),
            statuses={part for part in str(row["statuses"]).split("|") if part},
            warnungen=[str(value) for value in _load_json(row["warnungen_json"], [])],
            kommentare=[str(value) for value in _load_json(row["kommentare_json"], [])],
        )
        return StoredGruppe(
            id=int(row["id"]),
            durchgang_id=int(row["durchgang_id"]),
            bogen_id=None if row["bogen_id"] is None else int(row["bogen_id"]),
            gruppe=gruppe,
            quelle=str(row["quelle"]),
            ergebnis_status=str(row["ergebnis_status"]),
            konflikt_id=None if row["konflikt_id"] is None else int(row["konflikt_id"]),
        )

    # -- Konflikte -------------------------------------------------------

    def create_konflikt(
        self,
        *,
        durchgang_id: int,
        spieler_nr: str,
        gruppe_a_id: int,
        gruppe_b_id: int,
    ) -> Konflikt:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO konflikt
                    (durchgang_id, spieler_nr, gruppe_a_id, gruppe_b_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (durchgang_id, spieler_nr, gruppe_a_id, gruppe_b_id, _now()),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite hat keine Konflikt-ID vergeben.")
            konflikt_id = int(cursor.lastrowid)
        return Konflikt(
            id=konflikt_id,
            durchgang_id=durchgang_id,
            spieler_nr=spieler_nr,
            gruppe_a_id=gruppe_a_id,
            gruppe_b_id=gruppe_b_id,
            status="offen",
            gewaehlt_gruppe_id=None,
        )

    def list_offene_konflikte(self, durchgang_id: int) -> list[Konflikt]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM konflikt WHERE durchgang_id = ? AND status = 'offen'",
                (durchgang_id,),
            ).fetchall()
        return [self._konflikt_from_row(row) for row in rows]

    def get_konflikt(self, konflikt_id: int) -> Konflikt | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM konflikt WHERE id = ?", (konflikt_id,)
            ).fetchone()
        if row is None:
            return None
        return self._konflikt_from_row(row)

    def update_konflikt(
        self, konflikt_id: int, *, status: str, gewaehlt_gruppe_id: int | None
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE konflikt SET status = ?, gewaehlt_gruppe_id = ?
                WHERE id = ?
                """,
                (status, gewaehlt_gruppe_id, konflikt_id),
            )

    @staticmethod
    def _konflikt_from_row(row: sqlite3.Row) -> Konflikt:
        return Konflikt(
            id=int(row["id"]),
            durchgang_id=int(row["durchgang_id"]),
            spieler_nr=str(row["spieler_nr"]),
            gruppe_a_id=int(row["gruppe_a_id"]),
            gruppe_b_id=int(row["gruppe_b_id"]),
            status=str(row["status"]),
            gewaehlt_gruppe_id=(
                None
                if row["gewaehlt_gruppe_id"] is None
                else int(row["gewaehlt_gruppe_id"])
            ),
        )

    # -- App-State und Backup -------------------------------------------

    def set_last_opened(self, turnier_id: int) -> None:
        self._set_state("last_opened_turnier", str(turnier_id))

    def get_last_opened_id(self) -> int | None:
        return self._get_int_state("last_opened_turnier")

    def clear_last_opened(self) -> None:
        self._clear_state("last_opened_turnier")

    def set_last_opened_durchgang(self, durchgang_id: int) -> None:
        self._set_state("last_opened_durchgang", str(durchgang_id))

    def get_last_opened_durchgang_id(self) -> int | None:
        return self._get_int_state("last_opened_durchgang")

    def set_undo(self, data: dict[str, object]) -> None:
        self._set_state("undo", json.dumps(data, ensure_ascii=False))

    def get_undo(self) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = 'undo'"
            ).fetchone()
        if row is None:
            return None
        try:
            data = json.loads(str(row["value"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def clear_undo(self) -> None:
        self._clear_state("undo")

    def _set_state(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_state (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def _get_int_state(self, key: str) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            return None

    def _clear_state(self, key: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM app_state WHERE key = ?", (key,))

    def backup(self) -> Path:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        destination = self.path.with_name(f"{self.path.name}.{stamp}.bak")
        source_connection = self._connect()
        target_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(target_connection)
        finally:
            target_connection.close()
            source_connection.close()
        return destination


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_json(value: object, default: list[object]) -> list[object]:
    if not value:
        return list(default)
    try:
        loaded = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return list(default)
    return loaded if isinstance(loaded, list) else list(default)


def _int_or_none(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None
