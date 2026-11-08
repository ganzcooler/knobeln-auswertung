"""Eingangsordner nach neuen Scans durchsuchen."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .pdf import pdf_page_count

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | PDF_SUFFIXES


@dataclass(frozen=True)
class InputFile:
    path: Path
    relative: Path
    kind: str  # "image" | "pdf"


@dataclass
class ScanResult:
    files: list[InputFile]
    unsupported: list[Path]
    hidden: list[Path]


def scan_input(input_dir: Path) -> ScanResult:
    input_dir.mkdir(parents=True, exist_ok=True)
    files: list[InputFile] = []
    unsupported: list[Path] = []
    hidden: list[Path] = []

    for path in sorted(input_dir.rglob("*"), key=lambda p: str(p).lower()):
        if not path.is_file():
            continue
        relative = path.relative_to(input_dir)
        if any(part.startswith(".") for part in relative.parts):
            hidden.append(path)
            continue
        suffix = path.suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            files.append(InputFile(path=path, relative=relative, kind="image"))
        elif suffix in PDF_SUFFIXES:
            files.append(InputFile(path=path, relative=relative, kind="pdf"))
        else:
            unsupported.append(path)

    return ScanResult(files=files, unsupported=unsupported, hidden=hidden)


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def bogen_id_for(data: bytes, page: int = 1) -> str:
    return f"{short_hash(data)}-p{page}"


def page_count(file: InputFile, data: bytes) -> int:
    if file.kind == "pdf":
        return pdf_page_count(data)
    return 1


def bogen_ids_for(file: InputFile, data: bytes) -> list[str]:
    return [bogen_id_for(data, page) for page in range(1, page_count(file, data) + 1)]
