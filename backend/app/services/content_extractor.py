from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


class ExtractionError(Exception):
    pass


def extract_text(filename: str, data: bytes) -> tuple[str, str]:
    """Return (normalized text, detected source type)."""
    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".log", ".md", ".markdown", ".py", ".java", ".js", ".ts", ".tsx", ".jsx", ".sql", ".yaml", ".yml"}:
        return data.decode("utf-8", errors="replace"), _guess_text_type(suffix)

    if suffix in {".html", ".htm"}:
        soup = BeautifulSoup(data.decode("utf-8", errors="replace"), "html.parser")
        return soup.get_text("\n", strip=True), "html"

    if suffix == ".json":
        try:
            obj = json.loads(data.decode("utf-8", errors="replace"))
            return json.dumps(obj, ensure_ascii=False, indent=2), "json"
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"Invalid JSON: {exc}") from exc

    if suffix == ".csv":
        text = data.decode("utf-8", errors="replace")
        rows = list(csv.reader(io.StringIO(text)))
        return "\n".join(" | ".join(row) for row in rows), "csv"

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = [(page.extract_text() or "") for page in reader.pages]
            return "\n\n".join(pages), "pdf"
        except Exception as exc:
            raise ExtractionError(f"PDF extraction failed: {exc}") from exc

    if suffix == ".docx":
        try:
            from docx import Document

            document = Document(io.BytesIO(data))
            paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
            return "\n".join(paragraphs), "docx"
        except Exception as exc:
            raise ExtractionError(f"DOCX extraction failed: {exc}") from exc

    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}:
        try:
            from PIL import Image
            import pytesseract

            image = Image.open(io.BytesIO(data))
            return pytesseract.image_to_string(image), "image"
        except Exception as exc:
            raise ExtractionError(
                "Image OCR requires Pillow, pytesseract, and a local Tesseract installation. "
                f"OCR failed: {exc}"
            ) from exc

    raise ExtractionError(f"Unsupported file type: {suffix or 'no extension'}")


def _guess_text_type(suffix: str) -> str:
    mapping: dict[str, str] = {
        ".md": "markdown", ".markdown": "markdown", ".py": "code", ".java": "code",
        ".js": "code", ".ts": "code", ".tsx": "code", ".jsx": "code", ".sql": "code",
        ".yaml": "text", ".yml": "text",
    }
    return mapping.get(suffix, "text")


def content_stats(text: str) -> dict[str, Any]:
    words = text.split()
    lines = text.splitlines()
    return {
        "characters": len(text),
        "words": len(words),
        "lines": len(lines),
        "urls": sum(1 for token in words if token.startswith(("http://", "https://"))),
        "code_like": any(marker in text for marker in ["import ", "def ", "class ", "SELECT ", "function ", "const "]),
    }
