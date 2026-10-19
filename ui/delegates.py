from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from ui.results_model import format_percent
from ui.theme import TOKENS


def _draw_item_background(
    painter: QPainter, option: QStyleOptionViewItem, index
) -> None:
    """Let the style paint the base cell (selection, alternate row, focus)."""
    opt = QStyleOptionViewItem(option)
    style = opt.widget.style() if opt.widget else QApplication.style()
    style.drawPrimitive(
        QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, opt.widget
    )


class MatchDelegate(QStyledItemDelegate):
    """Paints a rounded match bar plus the percentage text."""

    def paint(self, painter: QPainter, option, index) -> None:
        value = index.data(Qt.ItemDataRole.UserRole)
        percent = None if value is None or value < 0 else float(value)

        painter.save()
        _draw_item_background(painter, option, index)

        rect = option.rect.adjusted(10, 0, -10, 0)
        text_width = 46
        bar_rect = QRectF(
            rect.left(),
            rect.center().y() - 4,
            max(8, rect.width() - text_width - 8),
            8,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2A2F3A"))
        painter.drawRoundedRect(bar_rect, 4, 4)

        if percent is not None:
            fill_width = max(4.0, bar_rect.width() * min(percent, 100.0) / 100.0)
            if percent >= 70:
                color = TOKENS["success"]
            elif percent >= 40:
                color = TOKENS["warning"]
            else:
                color = TOKENS["danger"]
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(
                QRectF(bar_rect.left(), bar_rect.top(), fill_width, bar_rect.height()),
                4,
                4,
            )

        painter.setPen(QColor(TOKENS["muted"] if percent is None else TOKENS["text"]))
        label = format_percent(percent)
        text_rect = option.rect.adjusted(0, 0, -10, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            label,
        )
        painter.restore()


class StatusDelegate(QStyledItemDelegate):
    """Paints the status as a small colored pill."""

    COLORS = {
        "OK": "success",
        "Scanned": "warning",
        "Encrypted": "danger",
        "Error": "danger",
    }

    def paint(self, painter: QPainter, option, index) -> None:
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        painter.save()
        _draw_item_background(painter, option, index)

        color = QColor(TOKENS[self.COLORS.get(text, "muted")])
        background = QColor(color)
        background.setAlpha(38)

        metrics = QFontMetrics(option.font)
        pill_width = max(52, metrics.horizontalAdvance(text) + 22)
        pill_height = 22
        pill = QRectF(
            option.rect.left() + 10,
            option.rect.center().y() - pill_height / 2,
            pill_width,
            pill_height,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(pill, 11, 11)

        painter.setPen(color)
        painter.drawText(
            pill,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        painter.restore()
