from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from core.models import STATUS_LABELS, ResultRow

STATUS_COLORS = {
    "OK": "#34D399",
    "SCANNED": "#FBBF24",
    "ENCRYPTED": "#F87171",
    "ERROR": "#F87171",
}


def format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value - round(value)) < 0.05:
        return f"{round(value)}%"
    return f"{value:.1f}%"


class ResultsModel(QAbstractTableModel):
    """Read-only table model backed by a list of ``ResultRow`` objects."""

    HEADERS = ("File", "Match %", "Matched keywords", "Missing keywords", "Status")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[ResultRow] = []

    # -- Qt model API -----------------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None

        row = self._rows[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return row.name
            if column == 1:
                return format_percent(row.percent)
            if column == 2:
                return ", ".join(row.matched)
            if column == 3:
                return ", ".join(row.missing)
            if column == 4:
                return STATUS_LABELS.get(row.status, row.status)
            return None

        if role == Qt.ItemDataRole.UserRole:
            # Used for sorting: numeric percentage, filename, or status.
            if column == 0:
                return row.name.lower()
            if column == 1:
                return -1.0 if row.percent is None else row.percent
            if column == 4:
                return row.status
            return " ".join(row.matched if column == 2 else row.missing).lower()

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column == 1:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if column == 4:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.ItemDataRole.ForegroundRole and column == 4:
            return QColor(STATUS_COLORS.get(row.status, "#8B93A5"))

        if role == Qt.ItemDataRole.ToolTipRole:
            if column == 0:
                return str(row.path)
            if column == 1 and row.percent is None:
                return "No percentage: this PDF could not be scored"
            if column == 2:
                return ", ".join(row.matched) or "No keywords matched"
            if column == 3:
                return ", ".join(row.missing) or "All keywords matched"
            if column == 4:
                return {
                    "OK": "Text extracted successfully",
                    "SCANNED": "Image-only PDF; OCR is not enabled",
                    "ENCRYPTED": "Password-protected PDF",
                    "ERROR": "Could not open this file as a PDF",
                }.get(row.status, row.status)
        return None

    # -- helpers ----------------------------------------------------------
    def rows(self) -> list[ResultRow]:
        return list(self._rows)

    def add_row(self, row: ResultRow) -> None:
        position = len(self._rows)
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.append(row)
        self.endInsertRows()

    def remove_rows(self, paths: set) -> None:
        if not paths or not self._rows:
            return
        self.beginResetModel()
        self._rows = [row for row in self._rows if row.path not in paths]
        self.endResetModel()

    def clear(self) -> None:
        if not self._rows:
            return
        self.beginResetModel()
        self._rows = []
        self.endResetModel()
