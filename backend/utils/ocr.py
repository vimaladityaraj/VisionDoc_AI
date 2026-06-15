"""OCR utilities for PDFs and image documents."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageOps

SUPPORTED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def extract_text(path: Path) -> str:
    """Extract text from a PDF/image using native text extraction plus OCR fallback."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".pdf":
        return _extract_pdf(path)
    return _extract_image(path)


def _extract_pdf(path: Path) -> str:
    parts: list[str] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if len(text) < 25:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(_preprocess_image(image))
            if text.strip():
                parts.append(f"--- Page {page_index} ---\n{text.strip()}")
    return "\n\n".join(parts).strip()


def _extract_image(path: Path) -> str:
    with Image.open(path) as image:
        return pytesseract.image_to_string(_preprocess_image(image)).strip()


def _preprocess_image(image: Image.Image) -> Image.Image:
    """Light preprocessing to improve OCR reliability on simple scans."""
    gray = ImageOps.grayscale(image)
    return ImageOps.autocontrast(gray)
