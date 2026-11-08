"""Lesen, Schreiben und Gruppieren der einen Auswertungs-CSV."""

from __future__ import annotations

import csv
import io
import os
import shutil
from collections import OrderedDict
from pathlib import Path

from ..domain.models import Gruppe
from .csv_mapping import gruppe_from_csv_rows, gruppe_to_rows

CSV_COLUMNS = [
    "Bogen_ID",
    "Quelle",
    "Seite",
    "Spieler_Position",
    "Durchgang_Nr",
    "Spieler_Nr",
    "Spieler_Name",
    "Wurf_Nr",
    "Punkte",
    "Punkte_Roh",
    "Korrektur",
    "Summe_Bogen_Roh",
    "Summe_Bogen",
    "Summe_Berechnet",
    "Delta",
    "Status",
    "Warnung",
    "Konflikt",
    "Konflikt_Detail",
    "Namenskonflikt",
    "Geprueft",
    "Kommentar",
]


class CSVWriteError(RuntimeError):
    pass


def _detect_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample.splitlines() else ""
    return ";" if first.count(";") >= first.count(",") else ","


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], list(CSV_COLUMNS)
    try:
        sample = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CSVWriteError(f"CSV konnte nicht gelesen werden: {exc}") from exc
    if not sample.strip():
        return [], list(CSV_COLUMNS)

    delimiter = _detect_delimiter(sample)
    reader = csv.DictReader(io.StringIO(sample, newline=""), delimiter=delimiter)
    fieldnames = list(reader.fieldnames or [])
    out_fields = list(CSV_COLUMNS) + [f for f in fieldnames if f not in CSV_COLUMNS]

    rows: list[dict[str, str]] = []
    for raw in reader:
        row = {name: (raw.get(name) or "") for name in out_fields}
        for key, value in raw.items():
            if key is not None and key not in row:
                row[key] = value or ""
        if not any(str(value).strip() for value in row.values()):
            continue
        rows.append(row)
    return rows, out_fields


def load_groups(path: Path) -> tuple[list[Gruppe], list[str]]:
    rows, fieldnames = read_rows(path)
    grouped: OrderedDict[tuple[str, str], list[dict[str, str]]] = OrderedDict()
    for row in rows:
        bogen_id = str(row.get("Bogen_ID", "")).strip()
        position = str(row.get("Spieler_Position", "")).strip()
        if not bogen_id and not position:
            continue
        grouped.setdefault((bogen_id, position), []).append(row)

    unknown_columns = [f for f in fieldnames if f not in CSV_COLUMNS]
    groups = [
        gruppe_from_csv_rows(group_rows, unknown_columns=unknown_columns)
        for group_rows in grouped.values()
    ]
    return groups, fieldnames


def write_groups(
    path: Path,
    groups: list[Gruppe],
    fieldnames: list[str] | None = None,
    *,
    backup: bool = False,
) -> None:
    out_fields = list(CSV_COLUMNS)
    if fieldnames:
        out_fields += [f for f in fieldnames if f not in out_fields]

    rows: list[dict[str, str]] = []
    for gruppe in groups:
        rows.extend(gruppe_to_rows(gruppe, out_fields))
    _write_rows(path, rows, out_fields, backup=backup)


def _write_rows(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
    *,
    backup: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                delimiter=";",
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n",
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({name: row.get(name, "") for name in fieldnames})
        if backup and path.exists():
            shutil.copy2(path, path.with_name(path.name + ".bak"))
        os.replace(tmp, path)
    except PermissionError as exc:
        _safe_unlink(tmp)
        raise CSVWriteError(
            f"CSV ist gesperrt oder nicht schreibbar: {path}. "
            "Bitte die Datei in Excel schließen und erneut versuchen."
        ) from exc
    except OSError as exc:
        _safe_unlink(tmp)
        raise CSVWriteError(f"CSV konnte nicht geschrieben werden: {exc}") from exc


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
