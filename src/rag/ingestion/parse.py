"""Parse PDFs and plain-text files into chunks.

ponytail: pypdf instead of docling — docling pulls multi-GB ML models at first run,
unworkable on workshop wifi. Upgrade to docling if OCR or table extraction is needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 1500  # chars (~375 tokens)
CHUNK_OVERLAP = 150


@dataclass
class ParsedChunk:
    source: str
    page: int | None
    chunk_index: int
    content: str
    metadata: dict


def _chunk(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 100:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def _parse_pdf(path: Path) -> list[tuple[str, int | None]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [(page.extract_text() or "", i + 1) for i, page in enumerate(reader.pages)]


def _parse_txt(path: Path) -> list[tuple[str, int | None]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [(text, None)]


def parse_file(path: Path) -> list[ParsedChunk]:
    if path.suffix.lower() == ".pdf":
        pages = _parse_pdf(path)
    elif path.suffix.lower() == ".txt":
        pages = _parse_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    idx = 0
    result = []
    for page_text, page_no in pages:
        for chunk in _chunk(page_text):
            result.append(
                ParsedChunk(
                    source=path.name,
                    page=page_no,
                    chunk_index=idx,
                    content=chunk,
                    metadata={},
                )
            )
            idx += 1
    return result
