"""Aufräumen des Eingangs nach erfolgreichem CSV-Schreiben."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.models import Gruppe


@dataclass
class FileResult:
    path: Path
    relative: Path
    bogen_ids: list[str]
    technical_error: bool = False
    unsupported: bool = False
    force_review: bool = False
    error: str = ""


@dataclass
class CleanupAction:
    path: Path
    relative: Path
    action: str  # "delete" | "review" | "keep"


@dataclass
class CleanupReport:
    deleted: int = 0
    moved: int = 0
    kept: int = 0
    failures: list[str] = field(default_factory=list)


def plan_actions(
    results: list[FileResult],
    groups_by_bogen: dict[str, list[Gruppe]],
    *,
    keep_input: bool = False,
) -> list[CleanupAction]:
    actions: list[CleanupAction] = []
    for result in results:
        if result.unsupported:
            actions.append(CleanupAction(result.path, result.relative, "keep"))
            continue
        if result.technical_error:
            actions.append(CleanupAction(result.path, result.relative, "keep"))
            continue

        if keep_input:
            actions.append(CleanupAction(result.path, result.relative, "keep"))
            continue

        if result.force_review:
            actions.append(CleanupAction(result.path, result.relative, "review"))
            continue

        relevant: list[Gruppe] = []
        for bogen_id in result.bogen_ids:
            relevant.extend(groups_by_bogen.get(bogen_id, []))

        if not relevant:
            actions.append(CleanupAction(result.path, result.relative, "keep"))
            continue

        offen = [gruppe for gruppe in relevant if gruppe.ist_offen()]
        if offen:
            actions.append(CleanupAction(result.path, result.relative, "review"))
        else:
            actions.append(CleanupAction(result.path, result.relative, "delete"))
    return actions


def execute_actions(
    actions: list[CleanupAction],
    review_dir: Path,
) -> CleanupReport:
    report = CleanupReport()
    for action in actions:
        if action.action == "keep":
            report.kept += 1
            continue
        if not action.path.exists():
            continue
        try:
            if action.action == "delete":
                action.path.unlink()
                report.deleted += 1
            elif action.action == "review":
                review_dir.mkdir(parents=True, exist_ok=True)
                dest = review_dir / action.relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    suffix = hashlib.sha256(
                        str(action.path).encode("utf-8")
                    ).hexdigest()[:8]
                    dest = dest.with_name(f"{dest.stem}-{suffix}{dest.suffix}")
                shutil.move(str(action.path), str(dest))
                report.moved += 1
        except OSError as exc:
            report.failures.append(f"{action.path}: {exc}")
    return report
