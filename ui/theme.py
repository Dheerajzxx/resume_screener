from __future__ import annotations

import re

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

TOKENS = {
    "bg": "#0F1115",
    "surface": "#171A21",
    "surface2": "#1E222B",
    "border": "#2A2F3A",
    "text": "#E6E8EE",
    "muted": "#8B93A5",
    "accent": "#7C5CFF",
    "accent_hover": "#8F74FF",
    "success": "#34D399",
    "warning": "#FBBF24",
    "danger": "#F87171",
}

# Tokens are substituted with a regex instead of str.format because QSS is full
# of literal braces that str.format would try to interpret.
QSS = """
QWidget { color: {text}; font-size: 13px; }
QMainWindow, QDialog { background: {bg}; }

QFrame#card {
    background: {surface};
    border: 1px solid {border};
    border-radius: 12px;
}
QLabel#h1 { font-size: 24px; font-weight: 700; }
QLabel#subtitle { color: {muted}; font-size: 13px; }
QLabel#step {
    color: {accent};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#muted { color: {muted}; }
QLabel#emptyTitle { color: {text}; font-size: 16px; font-weight: 600; }
QLabel#emptyBody { color: {muted}; font-size: 12px; }
QLabel#chip {
    background: #241F3D;
    border: 1px solid #3B3266;
    border-radius: 9px;
    color: #CFC6FF;
    font-size: 11px;
    padding: 3px 9px;
}
QLabel#danger { color: {danger}; }

QLineEdit, QSpinBox {
    background: {surface2};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: {accent};
}
QLineEdit:hover, QSpinBox:hover { border-color: #3A4150; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid {accent}; }
QLineEdit:disabled, QSpinBox:disabled { color: #5A6172; }

QComboBox {
    background: {surface2};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 20px;
}
QComboBox:hover { border-color: #3A4150; }
QComboBox:focus { border: 1px solid {accent}; }
QComboBox:disabled { color: #5A6172; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {accent};
    selection-color: white;
    outline: 0;
}
QComboBox QAbstractItemView::item { padding: 6px 10px; }

QPushButton {
    background: {surface2};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}
QPushButton:hover { border-color: {accent}; }
QPushButton:pressed { background: {surface}; }
QPushButton:disabled { color: #5A6172; background: {surface}; border-color: {surface2}; }

QPushButton#primary {
    background: {accent};
    border: none;
    color: white;
}
QPushButton#primary:hover { background: {accent_hover}; }
QPushButton#primary:pressed { background: #6A4BEB; }
QPushButton#primary:disabled { background: #3A3366; color: #8E88B8; }
QPushButton#primary[running="true"] { background: {danger}; color: #2A0C0C; }
QPushButton#primary[running="true"]:hover { background: #FB8A8A; }

QProgressBar {
    background: {surface2};
    border: none;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk { background: {accent}; border-radius: 5px; }

QTableView {
    background: {surface};
    alternate-background-color: #1A1E26;
    border: 1px solid {border};
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #2B2457;
    selection-color: {text};
    outline: 0;
}
QHeaderView::section {
    background: {surface2};
    color: {muted};
    border: none;
    border-bottom: 1px solid {border};
    padding: 8px 10px;
    font-weight: 600;
}
QTableView::item { padding: 4px 10px; }

QTextBrowser {
    background: {surface};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 8px;
    selection-background-color: {accent};
    selection-color: white;
}

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 4px;
    background: {surface2};
}
QCheckBox::indicator:hover { border-color: {accent}; }
QCheckBox::indicator:checked { background: {accent}; border-color: {accent}; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #333948; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #454C60; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { height: 10px; background: transparent; }
QScrollBar::handle:horizontal { background: #333948; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; height: 0; }

QMenuBar { background: {bg}; color: {text}; }
QMenuBar::item { padding: 4px 8px; background: transparent; }
QMenuBar::item:selected { background: {surface2}; border-radius: 4px; }
QMenu { background: {surface}; border: 1px solid {border}; padding: 6px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: {accent}; color: white; }
QMenu::separator { height: 1px; background: {border}; margin: 4px 8px; }

QToolTip {
    background: {surface2};
    color: {text};
    border: 1px solid {border};
    padding: 6px;
}
"""


def stylesheet() -> str:
    """Render the QSS, replacing ``{token}`` placeholders with palette values."""
    return re.sub(r"\{(\w+)\}", lambda match: TOKENS[match.group(1)], QSS)


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")  # consistent base across macOS versions

    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: TOKENS["bg"],
        QPalette.ColorRole.WindowText: TOKENS["text"],
        QPalette.ColorRole.Base: TOKENS["surface2"],
        QPalette.ColorRole.AlternateBase: TOKENS["surface"],
        QPalette.ColorRole.Text: TOKENS["text"],
        QPalette.ColorRole.Button: TOKENS["surface"],
        QPalette.ColorRole.ButtonText: TOKENS["text"],
        QPalette.ColorRole.BrightText: "#FFFFFF",
        QPalette.ColorRole.Highlight: TOKENS["accent"],
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.PlaceholderText: TOKENS["muted"],
        QPalette.ColorRole.ToolTipBase: TOKENS["surface2"],
        QPalette.ColorRole.ToolTipText: TOKENS["text"],
    }
    for role, value in colors.items():
        palette.setColor(role, QColor(value))

    disabled = QPalette.ColorGroup.Disabled
    palette.setColor(disabled, QPalette.ColorRole.Text, QColor("#5A6172"))
    palette.setColor(disabled, QPalette.ColorRole.ButtonText, QColor("#5A6172"))
    palette.setColor(disabled, QPalette.ColorRole.WindowText, QColor("#5A6172"))

    app.setPalette(palette)
    app.setFont(QFont(".AppleSystemUIFont", 13))
    app.setStyleSheet(stylesheet())
