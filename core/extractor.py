from __future__ import annotations

from pathlib import Path

import pymupdf

MIN_TEXT_CHARS = 50  # below this we treat the PDF as scanned/empty

# path -> mtime -> (text, status). Only read by the single scan worker.
_cache: dict[tuple[str, float], tuple[str, str]] = {}


def extract_text(pdf_path: Path) -> tuple[str, str]:
    """Return ``(text, status)`` where status is OK, SCANNED, ENCRYPTED or ERROR."""
    try:
        with pymupdf.open(pdf_path) as doc:
            if doc.needs_pass:
                return "", "ENCRYPTED"
            text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return "", "ERROR"

    if len(text.strip()) < MIN_TEXT_CHARS:
        return text, "SCANNED"
    return text, "OK"


def extract_text_cached(pdf_path: Path) -> tuple[str, str]:
    """Cached variant keyed by absolute path and modification time.

    Re-running a scan after changing keywords avoids parsing every PDF again,
    as long as the files have not changed.
    """
    try:
        mtime = pdf_path.stat().st_mtime
        key = (str(pdf_path.resolve()), mtime)
    except OSError:
        return "", "ERROR"

    cached = _cache.get(key)
    if cached is not None:
        return cached

    result = extract_text(pdf_path)
    _cache[key] = result
    return result


def clear_cache() -> None:
    _cache.clear()
