from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSettings,
    QSortFilterProxyModel,
    Qt,
    QThread,
    QUrl,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core import __version__
from core.export import export_csv
from core.matcher import Keyword, parse_keywords, qualifies
from core.models import ResultRow
from core.shortlist import FOLDER_NAME, shortlist
from ui.delegates import MatchDelegate, StatusDelegate
from ui.presets import PresetStore
from ui.results_model import ResultsModel
from ui.user_guide import UserGuideDialog
from ui.worker import ScanWorker

SETTINGS_ORG = "ResumeScreener"
SETTINGS_APP = "App"
MAX_CHIPS = 6


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings or QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._presets = PresetStore(self._settings)
        self._thread: QThread | None = None
        self._worker: ScanWorker | None = None
        self._scanning = False
        self._cancel_requested = False
        self._pdf_count = 0
        self._last_progress: tuple[int, int] = (0, 0)
        self._scanned_folder: Path | None = None
        self.export_action: QAction | None = None
        self._guide_dialog: UserGuideDialog | None = None

        self.setWindowTitle("Resume Screener")
        self.resize(1060, 830)
        self.setMinimumSize(900, 680)
        self.setAcceptDrops(True)

        self._build_ui()
        self._build_menu()
        self._restore_settings()
        self._refresh_state()

    # -- construction -----------------------------------------------------
    @staticmethod
    def _card() -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)
        return card

    @staticmethod
    def _step(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("step")
        return label

    def _build_ui(self) -> None:
        self.model = ResultsModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Resume Screener")
        title.setObjectName("h1")
        subtitle = QLabel("Rank PDF resumes against the keywords you care about.")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch(1)

        self.guide_btn = QPushButton("User Guide")
        self.guide_btn.setMinimumHeight(34)
        self.guide_btn.setToolTip("Open the in-app user guide")
        self.guide_btn.clicked.connect(self._show_user_guide)
        header.addWidget(self.guide_btn)
        layout.addLayout(header)

        layout.addWidget(self._build_folder_card())
        layout.addWidget(self._build_keywords_card())
        layout.addWidget(self._build_results_card(), 1)
        layout.addWidget(self._build_shortlist_card())

        self.setCentralWidget(central)

    def _build_folder_card(self) -> QFrame:
        card = self._card()
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.setSpacing(8)
        box.addWidget(self._step("STEP 1  ·  RESUME FOLDER"))

        row = QHBoxLayout()
        row.setSpacing(10)
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("/Users/you/Resumes")
        self.folder_edit.setClearButtonEnabled(True)
        self.folder_edit.setMinimumHeight(38)
        self.folder_edit.editingFinished.connect(self._refresh_folder_count)

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setMinimumHeight(38)
        self.browse_btn.clicked.connect(self._choose_folder)

        row.addWidget(self.folder_edit, 1)
        row.addWidget(self.browse_btn)
        box.addLayout(row)

        self.count_label = QLabel("No folder selected")
        self.count_label.setObjectName("muted")
        box.addWidget(self.count_label)
        return card

    def _build_keywords_card(self) -> QFrame:
        card = self._card()
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self._step("STEP 2  ·  KEYWORDS"))
        header.addStretch(1)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(170)
        self.preset_combo.setMaximumWidth(230)
        self.preset_combo.setMinimumHeight(32)
        self.preset_combo.setToolTip("Load a saved keyword preset")
        self.preset_combo.activated.connect(self._on_preset_activated)
        self.preset_combo.currentIndexChanged.connect(self._update_preset_buttons)
        header.addWidget(self.preset_combo)

        self.save_preset_btn = QPushButton("Save preset…")
        self.save_preset_btn.setMinimumHeight(32)
        self.save_preset_btn.setToolTip(
            "Save the current keywords, including weights, as a preset"
        )
        self.save_preset_btn.clicked.connect(self._on_save_preset)
        header.addWidget(self.save_preset_btn)

        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.setMinimumHeight(32)
        self.delete_preset_btn.clicked.connect(self._on_delete_preset)
        header.addWidget(self.delete_preset_btn)
        box.addLayout(header)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("python:3, django, sql, aws, js|javascript")
        self.keyword_edit.setMinimumHeight(40)
        self.keyword_edit.textChanged.connect(self._on_keywords_changed)

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setMinimumWidth(170)
        self.start_btn.clicked.connect(self._on_start_clicked)

        row.addWidget(self.keyword_edit, 1)
        row.addWidget(self.start_btn)
        box.addLayout(row)

        chips = QWidget()
        self.chips_layout = QHBoxLayout(chips)
        self.chips_layout.setContentsMargins(2, 0, 2, 0)
        self.chips_layout.setSpacing(6)
        box.addWidget(chips)

        hint = QLabel(
            "Separate keywords with commas. Use | for alternatives "
            "(js|javascript) and :N for weight (python:3)."
        )
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        box.addWidget(hint)
        return card

    def _build_results_card(self) -> QFrame:
        card = self._card()
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._step("RESULTS"))
        header.addStretch(1)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search files…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMaximumWidth(220)
        self.search_edit.setMinimumHeight(32)
        self.search_edit.textChanged.connect(self.proxy.setFilterFixedString)
        self.search_edit.textChanged.connect(self._update_export_button)
        header.addWidget(self.search_edit)

        self.export_btn = QPushButton("Export CSV…")
        self.export_btn.setMinimumHeight(32)
        self.export_btn.setToolTip(
            "Export the visible rows in their current order"
        )
        self.export_btn.clicked.connect(self._on_export_csv)
        header.addWidget(self.export_btn)
        box.addLayout(header)

        self.proxy.rowsInserted.connect(self._update_export_button)
        self.proxy.rowsRemoved.connect(self._update_export_button)
        self.proxy.modelReset.connect(self._update_export_button)
        self.proxy.layoutChanged.connect(self._update_export_button)

        self.stack = QStackedWidget()
        self.stack.setMinimumHeight(200)
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.empty_page = QWidget()
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setContentsMargins(20, 20, 20, 20)
        empty_layout.addStretch(1)
        self.empty_title = QLabel("No results yet")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_body = QLabel(
            "Select a folder, enter some keywords, then start processing."
        )
        self.empty_body.setObjectName("emptyBody")
        self.empty_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_body.setWordWrap(True)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_body)
        empty_layout.addStretch(1)
        self.stack.addWidget(self.empty_page)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setItemDelegateForColumn(1, MatchDelegate(self.table))
        self.table.setItemDelegateForColumn(4, StatusDelegate(self.table))
        self.table.doubleClicked.connect(self._open_result)

        table_header = self.table.horizontalHeader()
        table_header.setHighlightSections(False)
        table_header.setStretchLastSection(False)
        table_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        table_header.resizeSection(0, 230)
        table_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table_header.resizeSection(1, 150)
        table_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table_header.resizeSection(4, 112)
        self.stack.addWidget(self.table)
        self.stack.setCurrentWidget(self.empty_page)
        box.addWidget(self.stack, 1)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress_label = QLabel("0 / 0")
        self.progress_label.setObjectName("muted")
        self.progress_label.setMinimumWidth(112)
        self.progress_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.progress_label)
        box.addLayout(progress_row)
        return card

    def _build_shortlist_card(self) -> QFrame:
        card = self._card()
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.setSpacing(8)
        box.addWidget(self._step("STEP 3  ·  SHORTLIST"))

        controls = QHBoxLayout()
        controls.setSpacing(10)
        label = QLabel("Minimum match")
        label.setObjectName("muted")
        controls.addWidget(label)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(70)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threshold_spin.setFixedWidth(92)
        self.threshold_spin.setMinimumHeight(36)
        self.threshold_spin.valueChanged.connect(self._update_qualifying)
        controls.addWidget(self.threshold_spin)

        self.copy_check = QCheckBox("Copy instead of move")
        self.copy_check.setChecked(True)
        controls.addWidget(self.copy_check)
        controls.addStretch(1)
        box.addLayout(controls)

        footer = QHBoxLayout()
        self.qualify_label = QLabel("No resumes scanned yet")
        self.qualify_label.setObjectName("muted")
        footer.addWidget(self.qualify_label)
        footer.addStretch(1)

        self.shortlist_btn = QPushButton("Shortlist")
        self.shortlist_btn.setObjectName("primary")
        self.shortlist_btn.setMinimumWidth(150)
        self.shortlist_btn.setMinimumHeight(38)
        self.shortlist_btn.clicked.connect(self._on_shortlist)
        footer.addWidget(self.shortlist_btn)
        box.addLayout(footer)
        return card

    def _build_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        open_action = QAction("Open Folder…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._choose_folder)
        file_menu.addAction(open_action)

        self.export_action = QAction("Export CSV…", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.setEnabled(False)
        self.export_action.triggered.connect(self._on_export_csv)
        file_menu.addAction(self.export_action)

        start_action = QAction("Start Processing", self)
        start_action.setShortcut(QKeySequence("Ctrl+Return"))
        start_action.triggered.connect(self._on_start_clicked)
        file_menu.addAction(start_action)
        file_menu.addSeparator()

        quit_action = QAction("Quit Resume Screener", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setMenuRole(QAction.MenuRole.QuitRole)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu.addMenu("&Help")
        guide_action = QAction("User Guide", self)
        guide_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        guide_action.triggered.connect(self._show_user_guide)
        help_menu.addAction(guide_action)
        help_menu.addSeparator()

        about_action = QAction("About Resume Screener", self)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # -- settings ---------------------------------------------------------
    def _restore_settings(self) -> None:
        geometry = self._settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        folder = self._settings.value("folder", "", type=str)
        keywords = self._settings.value("keywords", "", type=str)
        threshold = self._settings.value("threshold", 70, type=int)
        copy_files = self._settings.value("copy", True, type=bool)

        if folder:
            self.folder_edit.setText(folder)
        if keywords:
            self.keyword_edit.setText(keywords)
        self.threshold_spin.setValue(max(0, min(100, int(threshold))))
        self.copy_check.setChecked(bool(copy_files))
        self._refresh_folder_count()
        self._refresh_presets()

    def _save_settings(self) -> None:
        self._settings.setValue("folder", self.folder_edit.text().strip())
        self._settings.setValue("keywords", self.keyword_edit.text())
        self._settings.setValue("threshold", self.threshold_spin.value())
        self._settings.setValue("copy", self.copy_check.isChecked())
        self._settings.setValue("window/geometry", self.saveGeometry())

    # -- folder handling --------------------------------------------------
    def _choose_folder(self) -> None:
        start_dir = self.folder_edit.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select resume folder",
            start_dir,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._set_folder(folder)

    def _set_folder(self, folder: str | Path) -> None:
        self.folder_edit.setText(str(folder))
        self._refresh_folder_count()

    def _pdf_files(self, folder: Path) -> list[Path]:
        try:
            files = [
                path
                for path in folder.iterdir()
                if path.is_file() and path.suffix.lower() == ".pdf"
            ]
        except OSError:
            return []
        return sorted(files, key=lambda path: path.name.lower())

    def _refresh_folder_count(self) -> None:
        raw = self.folder_edit.text().strip()
        if not raw:
            self._pdf_count = 0
            self.count_label.setText("No folder selected")
            self._refresh_state()
            return

        folder = Path(raw).expanduser()
        if not folder.is_dir():
            self._pdf_count = 0
            self.count_label.setText("Folder not found")
            self._refresh_state()
            return

        if (
            self.model.rowCount()
            and not self._scanning
            and self._scanned_folder is not None
            and folder.resolve() != self._scanned_folder.resolve()
        ):
            self._clear_results(
                "Folder changed",
                "Start processing to scan the newly selected folder.",
            )

        self._pdf_count = len(self._pdf_files(folder))
        if self._pdf_count == 0:
            self.count_label.setText("No PDF files found in this folder")
        elif self._pdf_count == 1:
            self.count_label.setText("1 PDF file found")
        else:
            self.count_label.setText(f"{self._pdf_count} PDF files found")
        self._refresh_state()

    def _current_folder(self) -> Path | None:
        raw = self.folder_edit.text().strip()
        if not raw:
            return None
        folder = Path(raw).expanduser()
        return folder if folder.is_dir() else None

    def _current_keywords(self) -> list[Keyword]:
        return parse_keywords(self.keyword_edit.text())

    # -- keyword chips ----------------------------------------------------
    def _on_keywords_changed(self) -> None:
        keywords = self._current_keywords()
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not keywords:
            placeholder = QLabel("No keywords yet")
            placeholder.setObjectName("muted")
            self.chips_layout.addWidget(placeholder)
        else:
            for keyword in keywords[:MAX_CHIPS]:
                text = keyword.display
                text = text if len(text) <= 18 else f"{text[:17]}…"
                chip = QLabel(text)
                chip.setObjectName("chip")
                chip.setToolTip(
                    keyword.text
                    if keyword.weight == 1
                    else f"{keyword.text} (weight {keyword.weight})"
                )
                self.chips_layout.addWidget(chip)
            if len(keywords) > MAX_CHIPS:
                more = QLabel(f"+{len(keywords) - MAX_CHIPS} more")
                more.setObjectName("muted")
                self.chips_layout.addWidget(more)

        self.chips_layout.addStretch(1)
        self._update_start_button()
        self._update_preset_buttons()

    # -- presets ----------------------------------------------------------
    def _refresh_presets(self, select: str | None = None) -> None:
        current = select if select is not None else self.preset_combo.currentData()
        names = self._presets.names()

        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("Load preset…", None)
        for name in names:
            self.preset_combo.addItem(name, name)
        index = self.preset_combo.findData(current) if current else -1
        self.preset_combo.setCurrentIndex(index if index >= 0 else 0)
        self.preset_combo.blockSignals(False)
        self._update_preset_buttons()

    def _update_preset_buttons(self) -> None:
        self.save_preset_btn.setEnabled(
            bool(self._current_keywords()) and not self._scanning
        )
        self.delete_preset_btn.setEnabled(
            bool(self.preset_combo.currentData()) and not self._scanning
        )

    def _on_preset_activated(self, index: int) -> None:
        name = self.preset_combo.itemData(index)
        if not name:
            return
        value = self._presets.get(name)
        if value is None:
            self._refresh_presets()
            return
        self.keyword_edit.setText(value)

    def _on_save_preset(self) -> None:
        raw = self.keyword_edit.text().strip()
        if not parse_keywords(raw):
            return

        suggested = self.preset_combo.currentData() or ""
        name, accepted = QInputDialog.getText(
            self,
            "Save preset",
            "Preset name:",
            QLineEdit.EchoMode.Normal,
            suggested,
        )
        if not accepted:
            return
        name = name.strip()
        if not name:
            return
        if "/" in name or "\\" in name:
            QMessageBox.warning(
                self,
                "Invalid preset name",
                "Preset names cannot contain slashes.",
            )
            return

        if self._presets.exists(name):
            answer = QMessageBox.question(
                self,
                "Overwrite preset",
                f"A preset named “{name}” already exists. Replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self._presets.save(name, raw)
        self._refresh_presets(select=name)

    def _on_delete_preset(self) -> None:
        name = self.preset_combo.currentData()
        if not name:
            return
        answer = QMessageBox.question(
            self,
            "Delete preset",
            f"Delete the preset “{name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._presets.delete(name)
        self._refresh_presets()

    # -- action state -----------------------------------------------------
    def _refresh_state(self) -> None:
        self._update_start_button()
        self._update_qualifying()
        self._update_export_button()

    def _update_start_button(self) -> None:
        if self._scanning:
            return
        ready = (
            self._pdf_count > 0
            and bool(self._current_keywords())
            and self._thread is None
        )
        self.start_btn.setEnabled(ready)
        if self._pdf_count == 0:
            self.start_btn.setToolTip("Choose a folder with PDF files first")
        elif not self._current_keywords():
            self.start_btn.setToolTip("Enter at least one keyword")
        else:
            self.start_btn.setToolTip("")

    def _update_qualifying(self) -> None:
        threshold = self.threshold_spin.value()
        count = sum(
            1 for row in self.model.rows() if qualifies(row.percent, threshold)
        )
        if count == 1:
            text = f"1 resume qualifies at {threshold}%"
        elif count > 1:
            text = f"{count} resumes qualify at {threshold}%"
        else:
            text = f"No resumes qualify at {threshold}%"
        self.qualify_label.setText(text)
        self.shortlist_btn.setEnabled(count > 0 and not self._scanning)

    def _update_export_button(self, *_args) -> None:
        enabled = self.proxy.rowCount() > 0 and not self._scanning
        self.export_btn.setEnabled(enabled)
        if self.export_action is not None:
            self.export_action.setEnabled(enabled)

    def _clear_results(self, title: str, body: str) -> None:
        self.model.clear()
        self.stack.setCurrentWidget(self.empty_page)
        self.empty_title.setText(title)
        self.empty_body.setText(body)
        self.progress.setValue(0)
        self.progress_label.setText("0 / 0")
        self._last_progress = (0, 0)
        self._refresh_state()

    def _set_running_style(self, running: bool) -> None:
        self.start_btn.setProperty("running", running)
        style = self.start_btn.style()
        style.unpolish(self.start_btn)
        style.polish(self.start_btn)
        self.start_btn.update()

    def _set_scanning_ui(self, scanning: bool) -> None:
        self.folder_edit.setEnabled(not scanning)
        self.browse_btn.setEnabled(not scanning)
        self.keyword_edit.setEnabled(not scanning)
        self.preset_combo.setEnabled(not scanning)
        self._set_running_style(scanning)
        self.start_btn.setText("Cancel" if scanning else "Start Processing")
        if scanning:
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("Stop scanning after the current file")
            self.shortlist_btn.setEnabled(False)
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setToolTip("")
        self._update_preset_buttons()
        self._update_export_button()

    # -- scanning ---------------------------------------------------------
    def _on_start_clicked(self) -> None:
        if self._scanning:
            self._cancel_scan()
            return
        if self._thread is not None:
            return

        folder = self._current_folder()
        if folder is None:
            return
        files = self._pdf_files(folder)
        keywords = self._current_keywords()
        if not files or not keywords:
            return
        self._start_scan(folder, files, keywords)

    def _start_scan(
        self, folder: Path, files: list[Path], keywords: list[Keyword]
    ) -> None:
        self.model.clear()
        self.stack.setCurrentWidget(self.empty_page)
        self.empty_title.setText("Scanning…")
        self.empty_body.setText(f"Reading {len(files)} PDF files.")
        self.search_edit.clear()
        self.progress.setValue(0)
        self.progress_label.setText(f"0 / {len(files)}")
        self._last_progress = (0, len(files))
        self._cancel_requested = False
        self._scanned_folder = folder
        self._scanning = True
        self._set_scanning_ui(True)
        self._update_qualifying()

        thread = QThread(self)
        worker = ScanWorker(files, keywords)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.row_ready.connect(self._on_row_ready)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_scan_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        thread.start()

    def _cancel_scan(self) -> None:
        if self._worker is None:
            return
        self._cancel_requested = True
        self._worker.cancel()
        self.start_btn.setText("Stopping…")
        self.start_btn.setEnabled(False)

    def _on_row_ready(self, row) -> None:
        self.model.add_row(row)
        if self.stack.currentWidget() is not self.table:
            self.stack.setCurrentWidget(self.table)
        self._update_qualifying()

    def _on_progress(self, done: int, total: int) -> None:
        self._last_progress = (done, total)
        self.progress.setValue(int(done / total * 100) if total else 0)
        self.progress_label.setText(f"{done} / {total}")

    def _on_scan_finished(self) -> None:
        if not self._scanning:
            return
        self._scanning = False
        self._set_scanning_ui(False)

        done, total = self._last_progress
        if self._cancel_requested:
            self.progress_label.setText(f"{done} / {total} · cancelled")
        elif total and done >= total:
            self.progress_label.setText(f"{done} / {total} · complete")

        if self.model.rowCount() == 0:
            self.stack.setCurrentWidget(self.empty_page)
            self.empty_title.setText("No results")
            self.empty_body.setText(
                "No resumes were processed. Check the folder and try again."
            )
        self._refresh_state()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._refresh_state()

    # -- results ----------------------------------------------------------
    def _open_result(self, proxy_index) -> None:
        source = self.proxy.mapToSource(proxy_index)
        rows = self.model.rows()
        if not 0 <= source.row() < len(rows):
            return
        path = rows[source.row()].path
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            QMessageBox.warning(
                self, "File not found", f"This file is no longer there:\n{path}"
            )

    def _qualifying_rows(self):
        threshold = self.threshold_spin.value()
        return [
            row for row in self.model.rows() if qualifies(row.percent, threshold)
        ]

    def _visible_rows(self) -> list[ResultRow]:
        """Rows in current table order, after search filtering and sorting."""
        source_rows = self.model.rows()
        visible: list[ResultRow] = []
        for proxy_row in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(proxy_row, 0))
            if source.isValid() and 0 <= source.row() < len(source_rows):
                visible.append(source_rows[source.row()])
        return visible

    def _on_export_csv(self) -> None:
        rows = self._visible_rows()
        if not rows:
            return

        folder = self._scanned_folder
        base = folder if folder is not None and folder.is_dir() else Path.home()
        suggested = base / "resume_results.csv"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export ranked results",
            str(suggested),
            "CSV files (*.csv)",
        )
        if not filename:
            return

        destination = Path(filename)
        if destination.suffix.lower() != ".csv":
            destination = destination.with_name(destination.name + ".csv")

        try:
            target = export_csv(rows, destination)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Export failed",
                f"Could not write the CSV file:\n{error}",
            )
            return

        done = QMessageBox(self)
        done.setIcon(QMessageBox.Icon.Information)
        done.setWindowTitle("Export complete")
        done.setText(
            f"Exported {len(rows)} result{'' if len(rows) == 1 else 's'} to CSV."
        )
        done.setInformativeText(str(target))
        open_button = done.addButton(
            "Open CSV", QMessageBox.ButtonRole.AcceptRole
        )
        done.addButton(QMessageBox.StandardButton.Close)
        done.exec()
        if done.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _on_shortlist(self) -> None:
        rows = self._qualifying_rows()
        if not rows:
            return
        folder = self._scanned_folder
        if folder is None or not folder.is_dir():
            QMessageBox.warning(
                self,
                "Folder unavailable",
                "The scanned folder is no longer available.",
            )
            return

        move = not self.copy_check.isChecked()
        verb = "move" if move else "copy"
        threshold = self.threshold_spin.value()

        confirm = QMessageBox(self)
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setWindowTitle("Shortlist resumes")
        confirm.setText(
            f"{verb.capitalize()} {len(rows)} resume"
            f"{'' if len(rows) == 1 else 's'} at {threshold}% or higher?"
        )
        confirm.setInformativeText(
            f"Destination: {folder / FOLDER_NAME}\n"
            f"Mode: {'move (originals leave this folder)' if move else 'copy (originals stay in place)'}"
        )
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.Ok)
        if confirm.exec() != QMessageBox.StandardButton.Ok:
            return

        try:
            target = shortlist([row.path for row in rows], folder, move=move)
        except OSError as error:
            QMessageBox.critical(
                self, "Shortlist failed", f"Could not shortlist the resumes:\n{error}"
            )
            return

        if move:
            # Originals have left the scanned folder; remove their stale rows.
            moved = {row.path for row in rows}
            self.model.remove_rows(moved)
            if self.model.rowCount() == 0:
                self._clear_results(
                    "All matches moved",
                    "The shortlisted resumes have left this folder. "
                    "Start processing to rescan it.",
                )
            else:
                self._refresh_state()

        done = QMessageBox(self)
        done.setIcon(QMessageBox.Icon.Information)
        done.setWindowTitle("Shortlist complete")
        done.setText(
            f"{len(rows)} resume{'' if len(rows) == 1 else 's'} "
            f"{'moved' if move else 'copied'} to {FOLDER_NAME}."
        )
        done.setInformativeText(str(target))
        open_button = done.addButton(
            "Open Shortlisted folder", QMessageBox.ButtonRole.AcceptRole
        )
        done.addButton(QMessageBox.StandardButton.Close)
        done.exec()
        if done.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    # -- misc -------------------------------------------------------------
    def _show_user_guide(self) -> None:
        if self._guide_dialog is None:
            self._guide_dialog = UserGuideDialog(self)
        self._guide_dialog.show()
        self._guide_dialog.raise_()
        self._guide_dialog.activateWindow()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Resume Screener",
            f"<b>Resume Screener {__version__}</b><br>"
            "Rank a folder of PDF resumes against your keywords.<br><br>"
            "Built with PySide6 and PyMuPDF. Shortlisting copies by default "
            "so your originals stay safe.",
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls() and any(
            url.isLocalFile() and Path(url.toLocalFile()).is_dir()
            for url in mime.urls()
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir():
                self._set_folder(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def closeEvent(self, event) -> None:
        if self._worker is not None:
            self._worker.cancel()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
        self._save_settings()
        super().closeEvent(event)
