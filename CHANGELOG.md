# Changelog

All notable changes to this project are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 - 2026-10-19

### Added

- macOS arm64 desktop app built with Python 3.12, PySide6, and PyMuPDF.
- Folder picker and drag-and-drop PDF input with a live PDF count.
- Comma-separated keywords with `js|javascript` alternatives and `python:3`
  weighting.
- Background PDF scanning with progress, cancellation, and per-file status
  handling (OK, Scanned, Encrypted, Error).
- Ranked, sortable results table with match bars and status badges.
- Saved keyword presets backed by QSettings.
- Threshold-based shortlisting with copy (default) and move modes, collision-safe
  file names, and an `Shortlisted` output folder.
- CSV export of visible results with rank, status, keywords, and path.
- Dark theme, saved window/settings state, keyboard shortcuts, and a custom
  app icon.
- In-app user guide (Help → User Guide) plus `USER_GUIDE.md`.
- PyInstaller `.app` build script and GitHub Actions CI/release workflows.

### Known limitations

- OCR is not implemented; image-only PDFs are flagged as Scanned.
- Only top-level PDF files are processed.
- DOCX input and Excel export are not included.
- macOS builds are unsigned; Gatekeeper may require right-click → Open.
- Tesseract is installed for future OCR work but is not bundled in the app.
