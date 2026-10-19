from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core import __version__
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Resume Screener")
    app.setApplicationDisplayName("Resume Screener")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("ResumeScreener")
    app.setOrganizationDomain("resumescreener.local")
    apply_theme(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
