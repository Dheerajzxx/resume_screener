from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from core.extractor import extract_text_cached
from core.matcher import Keyword, score
from core.models import ResultRow


class ScanWorker(QObject):
    """Extract and score PDFs off the GUI thread.

    Emits one row per file so the table fills in progressively. ``cancel()`` is
    checked between files; a scan never aborts on a single unreadable resume.
    """

    progress = Signal(int, int)  # done, total
    row_ready = Signal(object)  # ResultRow
    finished = Signal()

    def __init__(self, files: list[Path], keywords: list[Keyword]) -> None:
        super().__init__()
        self._files = files
        self._keywords = keywords
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @Slot()
    def run(self) -> None:
        total = len(self._files)
        try:
            for index, path in enumerate(self._files, start=1):
                if self._cancelled:
                    break

                text, status = extract_text_cached(path)
                if status == "OK":
                    percent, matched, missing = score(text, self._keywords)
                    row = ResultRow(path, percent, matched, missing, "OK")
                else:
                    row = ResultRow(path, None, [], [], status)

                self.row_ready.emit(row)
                self.progress.emit(index, total)
        finally:
            self.finished.emit()
