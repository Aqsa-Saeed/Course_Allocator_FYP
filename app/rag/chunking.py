"""Paragraph/sentence-aware chunking with overlap. Chunks never span PDF pages,
so every citation can point at an exact page."""
import re

_SPLIT_LEVELS = ["\n\n", "\n", ". ", "; ", ", ", " "]


def _clean(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split(text: str, size: int, level: int = 0) -> list[str]:
    """Recursively split text into pieces <= size, preferring natural boundaries."""
    if len(text) <= size:
        return [text]
    if level >= len(_SPLIT_LEVELS):
        return [text[i : i + size] for i in range(0, len(text), size)]
    sep = _SPLIT_LEVELS[level]
    pieces = text.split(sep)
    if len(pieces) == 1:
        return _split(text, size, level + 1)
    out: list[str] = []
    for i, piece in enumerate(pieces):
        piece = piece + (sep if i < len(pieces) - 1 else "")
        out.extend(_split(piece, size, level + 1) if len(piece) > size else [piece])
    return out


def _tail_overlap(text: str, overlap: int) -> str:
    if overlap <= 0 or len(text) <= overlap:
        return text if overlap > 0 else ""
    tail = text[-overlap:]
    m = re.search(r"\s", tail)  # start on a word boundary
    return tail[m.end():] if m else tail


def chunk_segment(text: str, size: int, overlap: int) -> list[str]:
    text = _clean(text)
    if not text:
        return []
    pieces = _split(text, size)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > size:
            chunks.append(current.strip())
            current = _tail_overlap(current, overlap) + piece
        else:
            current += piece
    if current.strip():
        chunks.append(current.strip())
    # Drop tiny fragments (page numbers, stray headers) unless they are all we have.
    kept = [c for c in chunks if len(c) >= 40]
    return kept or chunks


def chunk_document(segments, size: int, overlap: int) -> list[tuple[int | None, str]]:
    """segments: [(page_number|None, text)] -> [(page_number|None, chunk_text)]"""
    result: list[tuple[int | None, str]] = []
    for page, text in segments:
        for c in chunk_segment(text, size, overlap):
            result.append((page, c))
    return result
