from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from core.models import STATUS_LABELS, ResultRow

HEADERS = (
    "Rank",
    "File",
    "Match %",
    "Matched keywords",
    "Missing keywords",
    "Status",
    "Path",
)


def _percent(value: float | None) -> str:
    """Numeric percentage for CSV analysis; blank when a file was not scored."""
    return "" if value is None else f"{value:g}"


def export_csv(rows: Iterable[ResultRow], destination: Path) -> Path:
    """Write ``rows`` to ``destination`` in their given order.

    The file is UTF-8 with a BOM so Excel opens accents correctly. Match % is
    numeric, keyword lists are semicolon-separated, and the first column is the
    row's position in the exported/visible order.
    """
    ranked = list(rows)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        for rank, row in enumerate(ranked, start=1):
            writer.writerow(
                [
                    rank,
                    row.name,
                    _percent(row.percent),
                    "; ".join(row.matched),
                    "; ".join(row.missing),
                    STATUS_LABELS.get(row.status, row.status),
                    str(row.path),
                ]
            )
    return destination
