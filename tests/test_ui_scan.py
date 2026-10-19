import csv
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
)

from core.models import ResultRow
from ui.main_window import MainWindow
from ui.results_model import ResultsModel
from ui.theme import apply_theme


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    apply_theme(application)
    yield application


def make_pdf(path, text):
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(str(path))
    doc.close()
    return path


def test_window_scans_a_folder_end_to_end(tmp_path, app):
    folder = tmp_path / "resumes"
    folder.mkdir()
    make_pdf(
        folder / "jane.pdf",
        "Python and SQL developer with eight years of backend experience.",
    )
    make_pdf(folder / "scan.pdf", "")
    (folder / "broken.pdf").write_bytes(b"not actually a pdf")

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    window = MainWindow(settings=settings)
    window.show()
    app.processEvents()

    window._set_folder(folder)
    window.keyword_edit.setText("python:3, sql, aws")
    app.processEvents()
    assert window.start_btn.isEnabled()

    chips = [
        window.chips_layout.itemAt(i).widget().text()
        for i in range(window.chips_layout.count())
        if window.chips_layout.itemAt(i).widget() is not None
        and window.chips_layout.itemAt(i).widget().objectName() == "chip"
    ]
    assert "python ×3" in chips

    window._on_start_clicked()
    assert window._thread is not None
    assert not window.export_btn.isEnabled()

    deadline = time.time() + 20
    while window._thread is not None and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert window._thread is None, "scan thread did not finish in time"
    app.processEvents()
    assert window.model.rowCount() == 3

    rows = {row.name: row for row in window.model.rows()}
    assert rows["jane.pdf"].status == "OK"
    assert rows["jane.pdf"].percent == 80.0
    assert rows["jane.pdf"].matched == ["python ×3", "sql"]
    assert rows["jane.pdf"].missing == ["aws"]
    assert rows["scan.pdf"].status == "SCANNED"
    assert rows["scan.pdf"].percent is None
    assert rows["broken.pdf"].status == "ERROR"
    assert window.stack.currentWidget() is window.table
    assert "1 resume qualifies" in window.qualify_label.text()
    assert window.export_btn.isEnabled()
    assert window.export_action.isEnabled()
    assert [row.name for row in window._visible_rows()] == [
        "jane.pdf",
        "broken.pdf",
        "scan.pdf",
    ]

    window.search_edit.setText("jane")
    app.processEvents()
    assert [row.name for row in window._visible_rows()] == ["jane.pdf"]
    window.search_edit.clear()
    app.processEvents()

    window.close()
    app.processEvents()


def test_saved_preset_loads_into_keyword_field(tmp_path, app):
    settings = QSettings(
        str(tmp_path / "preset_settings.ini"), QSettings.Format.IniFormat
    )
    window = MainWindow(settings=settings)
    window._presets.save("Backend", "python:3, sql")
    window._refresh_presets(select="Backend")

    index = window.preset_combo.findData("Backend")
    assert index > 0
    window.keyword_edit.clear()
    window._on_preset_activated(index)

    assert window.keyword_edit.text() == "python:3, sql"
    chips = [
        window.chips_layout.itemAt(i).widget().text()
        for i in range(window.chips_layout.count())
        if window.chips_layout.itemAt(i).widget() is not None
        and window.chips_layout.itemAt(i).widget().objectName() == "chip"
    ]
    assert "python ×3" in chips
    assert window.save_preset_btn.isEnabled()
    assert window.delete_preset_btn.isEnabled()
    window.close()


def test_user_guide_opens_from_header(tmp_path, app):
    settings = QSettings(
        str(tmp_path / "guide_settings.ini"), QSettings.Format.IniFormat
    )
    window = MainWindow(settings=settings)
    window.show()
    app.processEvents()

    window.guide_btn.click()
    app.processEvents()

    dialog = window._guide_dialog
    assert dialog is not None
    assert dialog.isVisible()
    assert "User Guide" in dialog.windowTitle()
    text = dialog.browser.toPlainText()
    assert "Weights" in text
    assert "Exporting CSV" in text
    rendered = dialog.browser.toHtml()
    assert "<h1" in rendered
    assert "<h2" in rendered
    assert "<pre" in rendered

    buttons = dialog.findChild(QDialogButtonBox)
    buttons.button(QDialogButtonBox.StandardButton.Close).click()
    app.processEvents()
    assert not dialog.isVisible()

    window.close()


def test_export_button_writes_visible_rows(tmp_path, app, monkeypatch):
    folder = tmp_path / "resumes"
    folder.mkdir()
    settings = QSettings(
        str(tmp_path / "export_settings.ini"), QSettings.Format.IniFormat
    )
    window = MainWindow(settings=settings)
    window._scanned_folder = folder
    window.model.add_row(
        ResultRow(folder / "strong.pdf", 100.0, ["python ×3"], [], "OK")
    )
    window.model.add_row(
        ResultRow(folder / "weak.pdf", 40.0, [], ["python ×3"], "OK")
    )
    app.processEvents()
    assert window.export_btn.isEnabled()

    target = tmp_path / "exported"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *args, **kwargs: (str(target), "CSV files (*.csv)")),
    )
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)

    window.export_btn.click()

    csv_path = tmp_path / "exported.csv"
    assert csv_path.exists()
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        data = list(csv.reader(handle))
    assert data[0][0] == "Rank"
    assert data[1][1] == "strong.pdf"
    assert data[1][2] == "100"
    assert data[2][1] == "weak.pdf"
    window.close()


def test_results_model_removes_rows_after_move(tmp_path, app):
    model = ResultsModel()
    keep = tmp_path / "keep.pdf"
    remove = tmp_path / "remove.pdf"
    model.add_row(ResultRow(keep, 90.0, ["python"], [], "OK"))
    model.add_row(ResultRow(remove, 80.0, [], ["sql"], "OK"))

    model.remove_rows({remove})

    assert [row.path for row in model.rows()] == [keep]
