# Resume Screener: Development Plan

> Historical planning document. The implemented app is documented in `README.md`
> and `USER_GUIDE.md`.

A native-feeling macOS desktop app (Apple silicon / M1) built with **Python + PySide6**. It reads a folder of PDF resumes, scores each one against a list of keywords, shows a ranked table, and moves (or copies) resumes above a chosen match percentage into a `Shortlisted` folder.

---

## 1. Goals and scope

| Item | Decision |
|---|---|
| Platform | macOS on Apple silicon (arm64) |
| Language | Python 3.12 |
| UI toolkit | PySide6 (Qt 6) with a custom dark theme |
| Input | A folder containing resumes in PDF format |
| Output | Ranked results table + `Shortlisted` subfolder |
| Distribution | Run from source first, then a double-clickable `.app` |

**Version 1 (must have)**
1. Folder picker
2. Comma-separated keyword entry
3. Start Processing button, with progress and no UI freeze
4. Results table with filename, match %, matched and missing keywords
5. Threshold input and Shortlist button
6. Shortlist folder created inside the selected folder if it does not exist

**Version 2 (later)**
- OCR for scanned PDFs
- Keyword weights (`python:3`)
- Export results to CSV or Excel
- Saved keyword presets
- Support for DOCX resumes

---

## 2. User flow

```
[Select Folder] -> [Enter Keywords] -> [Start Processing]
        -> [Results table, sorted by match %]
        -> [Enter threshold %] -> [Shortlist] -> files go to <folder>/Shortlisted
```

### Screen layout (single window)

```
+--------------------------------------------------------------+
|  Resume Screener                                    [ - o x ] |
+--------------------------------------------------------------+
|  STEP 1  Resume folder                                        |
|  [ /Users/me/Resumes                    ] [ Browse... ]       |
|  142 PDF files found                                          |
|--------------------------------------------------------------|
|  STEP 2  Keywords (comma separated)                           |
|  [ python, django, sql, aws, js|javascript, c++ ]             |
|  (chips preview:  python  django  sql  aws  js|javascript )   |
|                                         [ Start Processing ]  |
|--------------------------------------------------------------|
|  [==================== 68% ========]  97 / 142                |
|--------------------------------------------------------------|
|  Results                                       [Search....]   |
|  Name              Match %        Matched         Status      |
|  jane_doe.pdf      [#########-] 90%  python, sql…  OK         |
|  ravi_k.pdf        [######----] 60%  python, aws   OK         |
|  scan_017.pdf      --             --               Scanned    |
|--------------------------------------------------------------|
|  STEP 3  Shortlist                                            |
|  Minimum match: [ 70 ] %   [x] Copy instead of move           |
|  12 resumes qualify                       [ Shortlist ]       |
+--------------------------------------------------------------+
```

---

## 3. Technology stack

| Purpose | Package | Notes |
|---|---|---|
| GUI | `PySide6` | Official Qt for Python; arm64 wheels available |
| PDF text | `PyMuPDF` | Fast, accurate, arm64 wheels |
| Matching | `re` (stdlib) | Case-insensitive whole-word regex |
| File ops | `pathlib`, `shutil` (stdlib) | Create folder, copy or move |
| OCR (v2, optional) | `pytesseract` + `tesseract` (Homebrew) | For scanned resumes |
| Packaging | `pyinstaller` or `py2app` | Builds the `.app` |

System tools: Xcode Command Line Tools, Homebrew, Python 3.12.

---

## 4. Project structure

```
resume_screener/
├── install.sh                  # check-first installer (section 5)
├── run.sh                      # activates venv and starts the app
├── requirements.txt
├── app.py                      # entry point
├── core/
│   ├── __init__.py
│   ├── extractor.py            # PDF -> text, scanned detection
│   ├── matcher.py              # keyword parsing + scoring
│   ├── shortlist.py            # create folder, copy/move, collisions
│   └── models.py               # ResultRow dataclass
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # layout and signal wiring
│   ├── worker.py               # background processing thread
│   ├── results_model.py        # QAbstractTableModel
│   ├── delegates.py            # progress-bar cell painter
│   └── theme.py                # palette + QSS stylesheet
└── tests/
    ├── test_matcher.py
    └── test_shortlist.py
```

Rule: `core/` never imports Qt. That keeps the logic testable without opening a window.

`requirements.txt`
```
PySide6>=6.7
PyMuPDF>=1.24
pytesseract>=0.3.10
pyinstaller>=6.6
```

---

## 5. Installation: check first, install only what is missing

`install.sh` tests each dependency and installs it only if it is absent, so it is safe to run again and again.

```bash
#!/usr/bin/env bash
# install.sh - idempotent installer for Resume Screener (macOS, Apple silicon)
set -euo pipefail

GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RED="\033[0;31m"; NC="\033[0m"
ok()   { echo -e "${GREEN}[ok]${NC}   $1 (already installed, skipping)"; }
inst() { echo -e "${YELLOW}[install]${NC} $1"; }
die()  { echo -e "${RED}[error]${NC} $1"; exit 1; }

PY_VERSION="3.12"
VENV_DIR=".venv"
PIP_PACKAGES=("PySide6" "PyMuPDF" "pytesseract" "pyinstaller")

# 0. Platform check
[[ "$(uname -s)" == "Darwin" ]] || die "This installer is for macOS only."
if [[ "$(uname -m)" != "arm64" ]]; then
  echo -e "${YELLOW}[warn]${NC} Not an Apple silicon Mac (arm64). Continuing anyway."
fi

# 1. Xcode Command Line Tools
if xcode-select -p >/dev/null 2>&1; then
  ok "Xcode Command Line Tools"
else
  inst "Xcode Command Line Tools (a system dialog will open; finish it, then re-run this script)"
  xcode-select --install || true
  exit 0
fi

# 2. Homebrew
if command -v brew >/dev/null 2>&1; then
  ok "Homebrew"
else
  inst "Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
# Make sure brew is on PATH for this session (Apple silicon location)
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
command -v brew >/dev/null 2>&1 || die "Homebrew not found on PATH after install."

# 3. Python 3.12
if command -v "python${PY_VERSION}" >/dev/null 2>&1; then
  ok "Python ${PY_VERSION}"
else
  inst "Python ${PY_VERSION}"
  brew install "python@${PY_VERSION}"
fi
PYTHON_BIN="$(command -v python${PY_VERSION})"

# 4. Tesseract (optional OCR engine)
if brew list tesseract >/dev/null 2>&1; then
  ok "Tesseract OCR"
else
  inst "Tesseract OCR"
  brew install tesseract
fi

# 5. Virtual environment
if [[ -d "${VENV_DIR}" && -x "${VENV_DIR}/bin/python" ]]; then
  ok "Virtual environment (${VENV_DIR})"
else
  inst "Virtual environment (${VENV_DIR})"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# 6. Python packages (checked one by one)
python -m pip install --quiet --upgrade pip
for pkg in "${PIP_PACKAGES[@]}"; do
  if python -m pip show "${pkg}" >/dev/null 2>&1; then
    ok "pip: ${pkg}"
  else
    inst "pip: ${pkg}"
    python -m pip install "${pkg}"
  fi
done

# 7. Final verification
python - <<'EOF'
import importlib
for mod in ("PySide6", "pymupdf", "pytesseract"):
    importlib.import_module(mod)
print("All Python modules import correctly.")
EOF

echo -e "\n${GREEN}Setup complete.${NC} Start the app with: ./run.sh"
```

`run.sh`
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
python app.py
```

Make both executable and run the installer:
```bash
chmod +x install.sh run.sh
./install.sh
```

---

## 6. Core logic design

### 6.1 Extractor (`core/extractor.py`)

```python
from pathlib import Path
import pymupdf  # PyMuPDF

MIN_TEXT_CHARS = 50  # below this we treat the PDF as scanned/empty

def extract_text(pdf_path: Path) -> tuple[str, str]:
    """Return (text, status). status: OK | SCANNED | ENCRYPTED | ERROR"""
    try:
        with pymupdf.open(pdf_path) as doc:
            if doc.needs_pass:
                return "", "ENCRYPTED"
            text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return "", "ERROR"
    if len(text.strip()) < MIN_TEXT_CHARS:
        return text, "SCANNED"
    return text, "OK"
```

### 6.2 Matcher (`core/matcher.py`)

Scoring formula:

> **Match % = (keywords found ÷ total keywords) × 100**

Keyword syntax:
- `python, sql, aws` : three keywords
- `js|javascript` : one keyword with alternatives (any one counts)
- `c++`, `c#`, `.net` : special characters handled safely

```python
import re

def parse_keywords(raw: str) -> list[str]:
    seen, out = set(), []
    for k in raw.split(","):
        k = k.strip()
        if k and k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out

def _compile(keyword: str) -> re.Pattern:
    alts = [re.escape(a.strip()) for a in keyword.split("|") if a.strip()]
    # (?<!\w) / (?![\w+#]) = whole-word match that still works for C++, C#, .NET
    # and stops "C" from matching inside "C++" and "java" inside "javascript".
    pattern = r"(?<!\w)(?:" + "|".join(alts) + r")(?![\w+#])"
    return re.compile(pattern, re.IGNORECASE)

def score(text: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    matched, missing = [], []
    for kw in keywords:
        (matched if _compile(kw).search(text) else missing).append(kw)
    pct = round(len(matched) / len(keywords) * 100, 1) if keywords else 0.0
    return pct, matched, missing
```

### 6.3 Shortlist (`core/shortlist.py`)

```python
from pathlib import Path
import shutil

FOLDER_NAME = "Shortlisted"

def _unique(dest: Path) -> Path:
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({i}){dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def shortlist(files: list[Path], base_folder: Path, move: bool = False) -> Path:
    target = base_folder / FOLDER_NAME
    target.mkdir(exist_ok=True)           # create only if missing
    for f in files:
        dest = _unique(target / f.name)
        (shutil.move if move else shutil.copy2)(str(f), str(dest))
    return target
```

Rules:
- The `Shortlisted` folder is created in the selected folder only if it does not exist.
- Threshold uses `>=`.
- Default is **copy**. A "Move files instead" checkbox switches to move, so a wrong threshold never scrambles the original folder.
- Name collisions get a numeric suffix.
- Skip the `Shortlisted` folder itself when scanning for PDFs, so reruns do not process shortlisted copies.
- Scan only the top level of the folder (use `rglob` only if you add a "include subfolders" option).

### 6.4 Data model (`core/models.py`)

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ResultRow:
    path: Path
    percent: float | None          # None for unreadable files
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    status: str = "OK"             # OK | SCANNED | ENCRYPTED | ERROR
```

---

## 7. UI design and engineering

### 7.1 Threading (prevents a frozen window)

```python
from PySide6.QtCore import QObject, Signal, Slot
from core.extractor import extract_text
from core.matcher import score
from core.models import ResultRow

class ScanWorker(QObject):
    progress = Signal(int, int)        # done, total
    row_ready = Signal(object)         # ResultRow
    finished = Signal()

    def __init__(self, files, keywords):
        super().__init__()
        self.files, self.keywords = files, keywords
        self._cancel = False

    def cancel(self):
        self._cancel = True

    @Slot()
    def run(self):
        total = len(self.files)
        for i, f in enumerate(self.files, 1):
            if self._cancel:
                break
            text, status = extract_text(f)
            if status == "OK":
                pct, hit, miss = score(text, self.keywords)
                row = ResultRow(f, pct, hit, miss, "OK")
            else:
                row = ResultRow(f, None, [], [], status)
            self.row_ready.emit(row)
            self.progress.emit(i, total)
        self.finished.emit()
```

Usage in `main_window.py`: create a `QThread`, `worker.moveToThread(thread)`, connect `thread.started -> worker.run`, connect the worker's signals to UI slots, then `thread.start()`.

### 7.2 Results table

- `QTableView` with a custom `QAbstractTableModel` and a `QSortFilterProxyModel` (sort by match %, filter by filename).
- Columns: **File**, **Match %** (painted as a bar by a `QStyledItemDelegate`), **Matched keywords**, **Missing keywords**, **Status**.
- Row colour cue in the bar: green at 70% and above, amber at 40 to 69%, red below 40.
- Double-click a row to open the PDF in Preview (`QDesktopServices.openUrl(QUrl.fromLocalFile(...))`).
- Live counter under the table: "12 resumes qualify at 70%". It updates as the threshold changes.
- Scanned, encrypted and error rows show a status badge instead of a percentage and never qualify.

### 7.3 Controls and states

| Control | Behaviour |
|---|---|
| Browse | Opens `QFileDialog.getExistingDirectory`; shows the PDF count |
| Keywords | `QLineEdit` with a placeholder example; chip preview below |
| Start Processing | Disabled until a folder with PDFs and at least one keyword exist; becomes **Cancel** while running |
| Progress bar | Slim, accent-coloured, with "97 / 142" label |
| Threshold | `QSpinBox` 0 to 100 with a `%` suffix, default 70 |
| Shortlist | Disabled until results exist; confirms with a dialog that shows the count and copy/move mode |
| Completion | Toast or dialog with an "Open Shortlisted folder" button (`QDesktopServices`) |

### 7.4 Remember settings

Use `QSettings("ResumeScreener", "App")` to store the last folder, last keywords, threshold, copy/move choice and window size.

---

## 8. Dark theme

### 8.1 Design tokens

| Token | Hex | Use |
|---|---|---|
| `bg` | `#0F1115` | Window background |
| `surface` | `#171A21` | Cards / panels |
| `surface-2` | `#1E222B` | Inputs, table rows |
| `border` | `#2A2F3A` | Outlines and dividers |
| `text` | `#E6E8EE` | Primary text |
| `muted` | `#8B93A5` | Secondary text, placeholders |
| `accent` | `#7C5CFF` | Buttons, focus, progress |
| `accent-hover` | `#8F74FF` | Hover state |
| `success` | `#34D399` | High match |
| `warning` | `#FBBF24` | Medium match |
| `danger` | `#F87171` | Low match, errors |

Style: rounded corners (10 px cards, 8 px inputs), generous padding, 1 px subtle borders, one accent colour, no pure black or pure white, system font (SF Pro).

### 8.2 `ui/theme.py`

```python
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtWidgets import QApplication

TOKENS = dict(
    bg="#0F1115", surface="#171A21", surface2="#1E222B", border="#2A2F3A",
    text="#E6E8EE", muted="#8B93A5", accent="#7C5CFF", accent_hover="#8F74FF",
    success="#34D399", warning="#FBBF24", danger="#F87171",
)

def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")  # consistent base across macOS versions
    t = TOKENS
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(t["bg"]))
    pal.setColor(QPalette.WindowText, QColor(t["text"]))
    pal.setColor(QPalette.Base, QColor(t["surface2"]))
    pal.setColor(QPalette.AlternateBase, QColor(t["surface"]))
    pal.setColor(QPalette.Text, QColor(t["text"]))
    pal.setColor(QPalette.Button, QColor(t["surface"]))
    pal.setColor(QPalette.ButtonText, QColor(t["text"]))
    pal.setColor(QPalette.Highlight, QColor(t["accent"]))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.PlaceholderText, QColor(t["muted"]))
    app.setPalette(pal)
    app.setFont(QFont(".AppleSystemUIFont", 13))
    app.setStyleSheet(QSS.format(**t))

QSS = """
QWidget { color: {text}; font-size: 13px; }
QMainWindow, QDialog { background: {bg}; }

/* Cards */
QFrame#card {
    background: {surface};
    border: 1px solid {border};
    border-radius: 12px;
}
QLabel#h1 { font-size: 22px; font-weight: 700; }
QLabel#step { color: {accent}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#muted { color: {muted}; }

/* Inputs */
QLineEdit, QSpinBox {
    background: {surface2};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: {accent};
}
QLineEdit:hover, QSpinBox:hover { border-color: #3A4150; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid {accent}; }

/* Buttons */
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
QPushButton#primary:disabled { background: #3A3366; color: #8E88B8; }

/* Progress */
QProgressBar {
    background: {surface2};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk { background: {accent}; border-radius: 5px; }

/* Table */
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
QTableView::item { padding: 6px 10px; }

/* Checkbox */
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid {border}; border-radius: 4px; background: {surface2};
}
QCheckBox::indicator:checked { background: {accent}; border-color: {accent}; }

/* Scrollbars */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #333948; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #454C60; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { height: 10px; background: transparent; }
QScrollBar::handle:horizontal { background: #333948; border-radius: 4px; }

QToolTip { background: {surface2}; color: {text}; border: 1px solid {border}; padding: 6px; }
"""
```

> Note: the QSS block uses Python `str.format`. If you add any literal `{` or `}` (all QSS blocks have them), switch to `string.Template` with `$accent` style tokens, or double the braces (`{{` and `}}`). The simplest option is a small helper that replaces `{token}` with a regex substitution (`re.sub(r"\{(\w+)\}", lambda m: t[m.group(1)], QSS)`).

### 8.3 Polish checklist

- Cards wrapped in `QFrame#card` with `QGraphicsDropShadowEffect` (blur 24, alpha 80) for depth
- Match % bars drawn in the delegate with rounded ends and success/warning/danger colours
- Empty state: centred illustration text "Select a folder to begin"
- Drag and drop a folder onto the window to select it
- Keyword chips preview below the input
- Hover and focus states on every interactive element
- Smooth progress updates (throttle signals to about 30 per second for large folders)
- Native-feeling macOS menu bar (About, Quit), `Cmd+O` for Browse, `Cmd+Return` for Start
- App icon (`.icns`) for the Dock and the `.app` bundle

---

## 9. Edge cases and handling

| Case | Handling |
|---|---|
| Scanned / image-only PDF | Flag `SCANNED`, show in table, exclude from shortlist (OCR in v2) |
| Password-protected PDF | Flag `ENCRYPTED` |
| Corrupted PDF | Catch exception, flag `ERROR`, continue |
| Empty keyword list | Disable Start |
| Duplicate keywords | De-duplicate in `parse_keywords` |
| Folder has no PDFs | Show an empty-state message, disable Start |
| Keywords with `+`, `#`, `.` | Escaped and boundary-checked (section 6.2) |
| Shortlist folder already exists | Reuse it |
| Same filename already in Shortlisted | Add ` (1)`, ` (2)` suffix |
| Reprocessing after changing keywords | Clear table and rescan; optionally cache extracted text |
| macOS folder permission prompt | Normal on first access to Desktop, Documents, Downloads |
| User closes window mid-scan | Cancel the worker, join the thread, then quit |

---

## 10. Performance

- PyMuPDF reads a typical resume in tens of milliseconds, so 1,000 resumes take well under a minute on M1.
- Cache extracted text per file (keyed by path + modified time) so changing keywords is instant.
- If you ever need more speed, use `concurrent.futures.ProcessPoolExecutor` inside the worker for extraction.

---

## 11. Testing plan

**Unit tests (`pytest`)**
- `parse_keywords`: spacing, duplicates, empty entries
- `score`: `java` must not match `javascript`; `C++`, `C#`, `.NET` match correctly; case-insensitive; `js|javascript` alternatives; 0 keywords returns 0
- `shortlist`: folder creation, reuse of existing folder, collision suffix, copy vs move, threshold `>=` boundary

**Manual tests**
- 5 to 10 real resumes with different layouts (single column, two column, with tables)
- One scanned PDF, one password-protected PDF, one corrupted file
- A folder with 500+ PDFs to check responsiveness and cancel
- Paths with spaces and non-English characters
- Dark theme visual check on a Retina display and an external monitor

Install test: delete `.venv`, run `./install.sh`, then run it a second time. The second run must print `[ok]` for every item and install nothing.

---

## 12. Packaging as a Mac app

```bash
source .venv/bin/activate
pyinstaller --noconfirm --windowed --name "Resume Screener" \
            --icon assets/icon.icns app.py
# Result: dist/Resume Screener.app
```

Notes:
- Build on an Apple silicon Mac to get an arm64 binary.
- Unsigned apps trigger a Gatekeeper warning on other Macs (right-click, then Open). For wider distribution you need an Apple Developer ID for code signing and notarization.
- If you add OCR, the Tesseract binary is not bundled by PyInstaller. Either require Homebrew Tesseract on the target Mac or bundle it manually.

---

## 13. Milestones

| # | Milestone | Deliverable | Est. |
|---|---|---|---|
| 1 | Environment | `install.sh`, `run.sh`, empty window launches with dark theme | 0.5 day |
| 2 | Core logic | `extractor`, `matcher`, `shortlist` + unit tests passing | 1 day |
| 3 | UI skeleton | Folder picker, keyword input, buttons, theme applied | 1 day |
| 4 | Processing | Background worker, progress bar, cancel, results table | 1 day |
| 5 | Shortlist flow | Threshold, live counter, copy/move, confirmation, open folder | 0.5 day |
| 6 | Polish | Bar delegate, chips, empty states, shortcuts, saved settings, icon | 1 day |
| 7 | QA | Edge-case testing, fixes | 1 day |
| 8 | Package | `.app` build and test on a clean Mac | 0.5 day |

Total: roughly 6 to 7 working days for a polished version 1.

---

## 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scanned resumes score 0% | Good candidates missed | Flag clearly; add OCR in v2 |
| Keyword does not appear literally ("ML" vs "machine learning") | Under-scoring | Alternatives syntax `ml|machine learning` |
| Wrong threshold moves the wrong files | Messy folder | Copy by default plus a confirmation dialog |
| Raw keyword % ignores context (a skill mentioned once vs used for years) | Crude ranking | Weights and frequency scoring in v2 |
| Unsigned `.app` blocked on other Macs | Distribution friction | Document right-click Open, or sign and notarize |

---

## 15. Quick start

```bash
mkdir resume_screener && cd resume_screener
# 1. add install.sh, run.sh, requirements.txt and the source files from this plan
chmod +x install.sh run.sh
./install.sh     # checks everything, installs only what is missing
./run.sh         # launches the app
```