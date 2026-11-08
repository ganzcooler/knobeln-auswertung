#!/usr/bin/env python3
"""Vergleicht eine erzeugte auswertung.csv mit einem Golden-JSON."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def _groups(path: Path) -> dict[str, list[dict[str, str]]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig"), delimiter=";"))
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["Spieler_Nr"]].append(row)
    return groups


def _punkte(rows: list[dict[str, str]]) -> list[int | None]:
    ordered = sorted(rows, key=lambda row: int(row["Wurf_Nr"]))
    return [int(row["Punkte"]) if row["Punkte"] else None for row in ordered]


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_golden.py CSV GOLDEN", file=sys.stderr)
        return 2

    csv_path = Path(sys.argv[1])
    golden_path = Path(sys.argv[2])
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    groups = _groups(csv_path)
    diffs: list[str] = []

    for expected in golden["spieler"]:
        nr = expected["nr"]
        rows = groups.get(nr)
        if not rows:
            diffs.append(f"Spieler {nr}: fehlt in der CSV")
            continue

        actual_punkte = _punkte(rows)
        if actual_punkte != expected["punkte"]:
            diffs.append(
                f"Spieler {nr}: Punkte {actual_punkte} != {expected['punkte']}"
            )

        ordered = sorted(rows, key=lambda row: int(row["Wurf_Nr"]))
        actual_summe = (
            int(ordered[0]["Summe_Bogen"]) if ordered[0]["Summe_Bogen"] else None
        )
        if actual_summe != expected["summe_bogen"]:
            diffs.append(
                f"Spieler {nr}: Summe_Bogen {actual_summe} != {expected['summe_bogen']}"
            )

        actual_durchgang = (
            int(ordered[0]["Durchgang_Nr"]) if ordered[0]["Durchgang_Nr"] else None
        )
        if actual_durchgang != golden["durchgang_nr"]:
            diffs.append(
                f"Spieler {nr}: Durchgang {actual_durchgang} != "
                f"{golden['durchgang_nr']}"
            )

        expected_name = expected.get("name") or ""
        if expected_name and ordered[0]["Spieler_Name"] != expected_name:
            diffs.append(
                f"Spieler {nr}: Name {ordered[0]['Spieler_Name']!r} != "
                f"{expected_name!r}"
            )

    if diffs:
        for diff in diffs:
            print(f"DIFF: {diff}")
        return 1

    print(f"GOLDEN OK: {golden_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
