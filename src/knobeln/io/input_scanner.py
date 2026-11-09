"""Hilfen für Dateinamen und Bogen-IDs."""

from __future__ import annotations

import hashlib

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | PDF_SUFFIXES


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def bogen_id_for(data: bytes, page: int = 1) -> str:
    return f"{short_hash(data)}-p{page}"
