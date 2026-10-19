# Resume Screener — Project Knowledge

## What this is
A native-feeling macOS desktop app (Apple silicon) built with **Python 3.12 + PySide6**. It reads a folder of PDF resumes, scores each against user-entered keywords, shows a ranked table, and copies or moves resumes at or above a threshold into `<selected folder>/Shortlisted`.

Version **1.0.0** is implemented. `GOAL.md` remains the original product spec; `README.md` and `USER_GUIDE.md` are the user-facing docs.

## Commands
```bash
./install.sh                     # idempotent: checks Xcode CLT, Homebrew, Python 3.12,
                                 # Tesseract, then installs only missing pip packages
./run.sh                         # launch with .venv/bin/python app.py
.venv/bin/python -m pytest       # 62 tests (core + presets + CSV + guide + offscreen UI integration)
./build_app.sh                   # PyInstaller -> dist/Resume Screener.app
```
Manual equivalent: `source .venv/bin/activate && pytest`.
No linter/formatter is configured; code follows PEP 8 with 4-space indentation.

## Layout
```
app.py                  entry point: QApplication + dark theme + MainWindow
USER_GUIDE.md           end-user guide (source of truth for the in-app copy)
LICENSE                 MIT
CONTRIBUTING.md         dev setup, conventions, release process
SECURITY.md             private vulnerability reporting
CHANGELOG.md            release history (Keep a Changelog)
THIRD_PARTY_NOTICES.md  dependency licenses, incl. PyMuPDF AGPL and Qt LGPL
licenses/               full AGPL-3.0 and LGPL-3.0 texts (release assets)
CODE_OF_CONDUCT.md      contributor expectations
.github/                CI + tag release workflows, issue/PR templates, Dependabot
docs/                   README + user-guide screenshots
core/                   Qt-free domain logic
  extractor.py          PDF -> text; OK | SCANNED | ENCRYPTED | ERROR; mtime cache
  matcher.py            parse_keywords, score, qualifies
  export.py             ranked ResultRow list -> UTF-8 CSV (BOM)
  shortlist.py          create/reuse Shortlisted, collision-safe copy/move
  models.py             ResultRow dataclass + STATUS_LABELS
ui/
  main_window.py        layout, drag/drop, threading, shortlist flow, QSettings
  worker.py             ScanWorker moved onto a QThread
  presets.py            PresetStore: named keyword sets in QSettings
  user_guide.py         GUIDE_MARKDOWN + UserGuideDialog (modeless, QTextBrowser)
  results_model.py      QAbstractTableModel + percent formatting
  delegates.py          match-% bar and status badge painters
  theme.py              tokens, QPalette, brace-safe QSS rendering
tests/                  matcher, presets, CSV, guide, shortlist, extractor, headless UI scan
```
`core/` must never import Qt. Only `core.extractor` imports PyMuPDF.

## Release and versioning
- `core/__init__.py::__version__` is the app version (`1.0.0`); `app.py` sets it on `QApplication` and About displays it.
- `.github/workflows/ci.yml` runs tests + syntax checks on `macos-26` (arm64).
- `.github/workflows/release.yml` triggers on `v*` tags, verifies the tag matches `__version__`, tests, builds with `./build_app.sh`, zips `dist/Resume Screener.app`, writes `SHA256SUMS.txt`, uploads the artifact, and creates the GitHub release via `gh`.
- Release asset name: `Resume-Screener-<tag>-macOS-arm64.zip`. Builds are unsigned.
- Releases also attach `LICENSE`, `THIRD_PARTY_NOTICES.md`, and full `licenses/AGPL-3.0.txt` +
  `licenses/LGPL-3.0.txt` texts; keep them in sync when dependencies change.
- `build_app.sh` uses `.venv/bin/pyinstaller` when present, otherwise `pyinstaller` from PATH (CI).
- `requirements.txt` has upper bounds for reproducible release installs.

## Data flow
`MainWindow` lists top-level `*.pdf` files, parses keywords, then starts `ScanWorker` on a `QThread`.
For each file: `extract_text_cached` -> `score` -> `ResultRow` emitted via `row_ready`.
Rows are appended to `ResultsModel`, sorted/filtered by `QSortFilterProxyModel`, and painted by the delegates. Cancel is checked between files. A scan never aborts on one bad PDF.

Keywords are parsed into `Keyword(text, weight)` objects. Presets are stored by
`ui/presets.py` in the existing `QSettings` under the `presets` group; each value
is the raw comma-separated keyword text, so weights survive save/load.

CSV export takes `MainWindow._visible_rows()` (proxy order after search/sort)
and passes it to `core.export.export_csv`, so the file matches what the table
shows, including rank order.

## Matching semantics (keep these correct)
- Match % = `matched weight / total weight * 100`, rounded to 1 decimal; no keywords -> 0.0.
- Weights use a trailing positive integer: `python:3`, `js|javascript:2`. Default is 1; `:0` is clamped to 1. Non-numeric suffixes stay part of the keyword.
- Comma-separated keywords, de-duplicated case-insensitively by base text; the first occurrence keeps its weight. `a|b` is one keyword where either alternative counts.
- Whole-word matching with per-alternative boundaries:
  - leading `(?<!\w)` only when the alternative starts with a word character;
  - trailing `(?![\w+#])` always.
- Consequences: `java` does not match `javascript`; `C` does not match `C++`; `C++`/`C#` match literally; `.NET` matches both `.NET` and `ASP.NET`; matching is case-insensitive.
- Threshold qualification is inclusive (`>=`). Default 70.

## Presets
- `PresetStore` in `ui/presets.py` lists/saves/deletes named keyword sets in `QSettings` group `presets`.
- Names are trimmed; empty names and names containing `/` or `\` are rejected.
- The keyword card has a preset dropdown, **Save preset…**, and **Delete**. Save prompts for a name and confirms overwrite; loading sets the keyword field. Presets store the raw text, including weights.

## CSV export
- Triggered by **Export CSV…** in the results header or `Cmd+E`.
- Exports visible rows in current table order (search + sort applied), not just the qualifying subset.
- Columns: `Rank, File, Match %, Matched keywords, Missing keywords, Status, Path`.
- `Match %` is numeric (`80`, `66.7`) and blank for unreadable files; keyword lists use `; `.
- Written as `utf-8-sig` with `newline=""`; suggested filename is `<scanned folder>/resume_results.csv`.
- Export is disabled while scanning and when no rows are visible. `OSError` is shown in a critical dialog.

## Shortlist behavior
- Target is `<scanned folder>/Shortlisted`, created if missing and reused otherwise.
- **Copy is the default**; the checkbox "Copy instead of move" must be unticked to move.
- Name collisions get `name (1).pdf`, `name (2).pdf`, etc.
- After a move, the moved rows are removed from the table; if none remain the empty state explains the folder changed.
- Only top-level PDFs are scanned, so the `Shortlisted` folder is never reprocessed.
- Only readable rows (`percent is not None`) can qualify; scanned/encrypted/error rows never do.

## UI conventions
- Single window, three numbered cards (folder, keywords, shortlist) plus a results card.
- The user guide is reachable from the header **User Guide** button and **Help → User Guide** (`QKeySequence.StandardKey.HelpContents`). It opens a reusable modeless `UserGuideDialog`; Markdown is rendered by `QTextBrowser.setMarkdown`.
- `USER_GUIDE.md` is the source of truth. `ui/user_guide.py::GUIDE_MARKDOWN` embeds the same text; `tests/test_user_guide.py` fails if they drift.
- Theme tokens live in `ui/theme.py`; use them rather than ad-hoc colors.
- Match bar: success >= 70, warning 40–69, danger < 40. Status becomes a colored pill.
- Start is disabled until a valid folder with PDFs and at least one keyword is present; it becomes Cancel while scanning.
- Persist folder, keywords, threshold, copy/move, and window geometry with `QSettings("ResumeScreener", "App")`.
- Shortcuts: `Cmd+O` open folder, `Cmd+E` export CSV, `Cmd+Return` start/cancel. Double-click a row to open the PDF.

## Threading rules
- Never extract PDFs on the GUI thread.
- `ScanWorker` emits `progress(done, total)`, `row_ready(ResultRow)`, `finished()`.
- On finish: `thread.quit()`, then clean up refs in the `thread.finished` handler.
- On window close: cancel the worker, `thread.quit()`, `thread.wait(3000)`, then save settings.

## Gotchas
- **QSS is full of literal braces.** Do not call `str.format` on it; `ui/theme.py` substitutes only `{token}` via `re.sub`.
- `score()` accepts both `Keyword` objects and raw strings (for tests/compatibility). The UI and worker pass parsed `Keyword` objects.
- Preset names are QSettings keys, so slashes must stay rejected; otherwise a name would create a nested group.
- When editing the guide, update `USER_GUIDE.md` and copy the text into `GUIDE_MARKDOWN` (the sync test will catch mismatches). The in-app copy is embedded so the packaged `.app` does not depend on an external file.
- **PyMuPDF 2.0 auto-imports `pymupdf.layout`** (an optional ~50 MB ONNX layout stack) on `import pymupdf`, and PyInstaller does not collect its YAML/ONNX resources by default. That broke the first `.app` build. `build_app.sh` excludes `pymupdf.layout`, `pymupdf_layout`, `pymupdf4llm`, and `onnxruntime`; the upstream import is wrapped in `try/except ImportError`, and frozen extraction was verified. If layout analysis is ever needed, remove those excludes and add `--collect-data pymupdf`.
- Extracted text is cached in memory by absolute path + mtime, so changing keywords avoids re-parsing unchanged PDFs.
- Scanned/image-only PDFs are flagged and excluded; OCR is v2 (pytesseract/Tesseract are installed but unused).
- Folder changes clear stale results, since shortlisting must target the folder that produced the rows.
- macOS prompts for permission on first access to Desktop/Documents/Downloads.
- The `.app` is unsigned (Gatekeeper: right-click > Open). Tesseract is not bundled by PyInstaller.
- **Licensing constraint:** PyMuPDF is AGPL-3.0 or commercial, PySide6/Qt is LGPL-3.0/GPL. The repo code is MIT, but redistributing the bundled `.app` triggers AGPL/LGPL obligations; see `THIRD_PARTY_NOTICES.md`. Do not describe the packaged app as MIT-only without addressing this.
- Release CI must stay on an arm64 runner (`macos-26`, not `macos-26-intel`). Both workflows explicitly assert `uname -m == arm64`.
- The repository has not been initialized/pushed yet at the time these files were added; GitHub will need a remote and a `v1.0.0` tag for the release workflow to run.

## Verification state
- `pytest`: 62 passed, including weighted scoring, preset persistence, CSV export (core and UI button), user-guide content sync/rendering, and a headless (`QT_QPA_PLATFORM=offscreen`) end-to-end scan through the real window and worker thread.
- `install.sh` was run twice; the second run installed nothing and exited 0.
- `build_app.sh` produced an arm64 `.app` (`com.resumescreener.app`), which launched successfully offscreen.
- A frozen smoke binary exercised PyMuPDF extraction and scoring successfully with the layout exclusions.
- The GitHub Actions workflows were added but cannot be executed until the project is pushed to GitHub; `macos-26` arm64 runners are the intended targets.
