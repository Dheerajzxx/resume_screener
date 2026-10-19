from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

STATUS_LABELS = {
    "OK": "OK",
    "SCANNED": "Scanned",
    "ENCRYPTED": "Encrypted",
    "ERROR": "Error",
}


@dataclass
class ResultRow:
    """One scanned resume and its keyword result."""

    path: Path
    percent: float | None  # None for unreadable files
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    status: str = "OK"  # OK | SCANNED | ENCRYPTED | ERROR

    @property
    def name(self) -> str:
        return self.path.name
