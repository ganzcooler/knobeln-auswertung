"""Bild- und PDF-Vorverarbeitung für das Vision-Modell."""

from __future__ import annotations

import io

import pypdfium2 as pdfium
from PIL import Image, ImageOps

MAX_LONG_SIDE = 4000
JPEG_QUALITY = 95


def image_to_jpeg(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "LA"):
            background = Image.new("RGB", image.size, "white")
            alpha = image.getchannel("A")
            background.paste(image.convert("RGB"), mask=alpha)
            image = background
        else:
            image = image.convert("RGB")

        if max(image.size) > MAX_LONG_SIDE:
            ratio = MAX_LONG_SIDE / max(image.size)
            new_size = (
                max(1, int(image.width * ratio)),
                max(1, int(image.height * ratio)),
            )
            image = image.resize(new_size, Image.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return buffer.getvalue()


def pdf_page_count(data: bytes) -> int:
    with pdfium.PdfDocument(data) as pdf:
        return len(pdf)


def render_pdf_page(data: bytes, page_number: int, dpi: int = 300) -> bytes:
    """Rendert eine 1-basierte PDF-Seite als JPEG."""
    with pdfium.PdfDocument(data) as pdf:
        page = pdf[page_number - 1]
        try:
            bitmap = page.render(scale=dpi / 72)
            image = bitmap.to_pil().convert("RGB")
            if max(image.size) > MAX_LONG_SIDE:
                ratio = MAX_LONG_SIDE / max(image.size)
                new_size = (
                    max(1, int(image.width * ratio)),
                    max(1, int(image.height * ratio)),
                )
                image = image.resize(new_size, Image.LANCZOS)
            buffer = io.BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=JPEG_QUALITY,
                optimize=True,
            )
            return buffer.getvalue()
        finally:
            page.close()



