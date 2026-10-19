from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QTextBrowser,
    QVBoxLayout,
)

GUIDE_MARKDOWN = r"""# Resume Screener — User Guide

Resume Screener reads PDF resumes from one folder, scores each against your
keywords, and shows a ranked table. You can copy or move the strongest matches
into a `Shortlisted` folder and export the results as CSV.

This guide is also available inside the app: click **User Guide** in the header,
or use **Help → User Guide**.

## Before you start

- macOS on Apple silicon (arm64).
- Python 3.12, Xcode Command Line Tools, and Homebrew. The installer checks
  these and installs Python, Tesseract, and the Python packages if needed.
- Your resumes as PDF files. Scanned image-only PDFs can be ranked only as
  `Scanned`; OCR is not enabled in this version.

## Install and launch

From the project folder:

```bash
chmod +x install.sh run.sh build_app.sh
./install.sh
./run.sh
```

`install.sh` is safe to run repeatedly: it checks every dependency and installs
only what is missing.

To build a double-clickable app:

```bash
./build_app.sh
```

The result is `dist/Resume Screener.app`. The app is unsigned, so another Mac
may require right-click → Open the first time.

## Quick start

1. Click **Browse…** and choose the folder containing your PDF resumes.
2. Type keywords such as `python:3, django, sql, aws, js|javascript`.
3. Click **Start Processing**. The table fills in as each PDF is read.
4. Use the search box and column headers to filter and sort the results.
5. Optionally click **Export CSV…** to save the visible rows.
6. Set **Minimum match** and click **Shortlist**.
7. Matches are copied to `<selected folder>/Shortlisted` by default.

## The window

### Step 1 — Resume folder

**Browse…** opens a folder picker. You can also drag a folder onto the window.
The line under the field shows how many PDF files were found. Only the top
level of the folder is scanned; subfolders are not included.

### Step 2 — Keywords

Enter keywords separated by commas. The chips below the field preview what was
understood, including weights. **Start Processing** is enabled when the folder
has at least one PDF and at least one valid keyword.

While a scan is running, the same button becomes **Cancel**. It stops after the
current file finishes, so the app never freezes or leaves a half-written file.

### Results

The table shows the file name, weighted match percentage, matched keywords,
missing keywords, and a status. It is sorted by match percentage by default.

- **Search files…** filters the table by file name.
- Click a column header to change the sort.
- Double-click a row to open that PDF in your default viewer.
- The progress bar and counter show how many files have been processed.

### Step 3 — Shortlist

**Minimum match** is the inclusive cutoff (default 70%). The counter updates as
you change it. **Copy instead of move** is ticked by default so a wrong threshold
cannot rearrange your original folder.

## Keywords, alternatives, and weights

Keywords are case-insensitive and matched as whole words. `java` does not match
`javascript`, `C` does not match `C++`, and `sql` does not match `mysql`.

### Alternatives

Use `|` when one keyword can appear in several forms. These count as one keyword
where either spelling is accepted:

```text
js|javascript
ml|machine learning
```

### Weights

Add `:N` to give a keyword more influence:

```text
python:3, sql, aws
```

Match % is the share of total keyword weight that was found. In the example
above, Python is worth 3 and SQL and AWS are worth 1 each. If Python and SQL are
found but AWS is missing, the score is 4 out of 5, or 80%.

- The default weight is 1.
- Weights are positive integers. `:0` is treated as 1.
- A non-numeric suffix stays part of the keyword (for example `http://example`).
- Duplicate keywords keep the first occurrence and its weight.

### Presets

Use the preset dropdown, **Save preset…**, and **Delete** in the keyword card.

- **Save preset…** names the current keywords, weights included, and stores them
  with the app settings.
- Choose a preset from the dropdown to load it.
- Select a preset and click **Delete** to remove it.
- Preset names cannot contain slashes.

Presets survive restarts and are separate from the last-used keyword text.

## Understanding results

Status values:

- **OK** — text was extracted and scored.
- **Scanned** — the PDF has little or no selectable text. It is shown and
  excluded from shortlisting and CSV percentages.
- **Encrypted** — the PDF is password-protected and could not be read.
- **Error** — the file could not be opened as a PDF.

Files that are not `OK` have a blank percentage and never qualify. One bad file
does not stop the rest of the scan.

## Shortlisting files

Set a threshold and click **Shortlist**. A confirmation dialog shows the count
and whether the files will be copied or moved.

- The target is `<selected folder>/Shortlisted`.
- The folder is created if missing and reused if it already exists.
- Copy is the default; untick **Copy instead of move** to move originals.
- Name collisions become `name (1).pdf`, `name (2).pdf`, and so on. Nothing is
  overwritten.
- After a move, the moved rows are removed from the table. If none remain, the
  empty state explains that the folder can be rescanned.
- A completion dialog offers to open the Shortlisted folder.

## Exporting CSV

Click **Export CSV…** in the results header, or press `Cmd+E`, or use
**File → Export CSV…**.

The export contains exactly what the table shows: visible rows after the search
filter and in the current sort order. The default name is
`resume_results.csv` in the scanned folder.

Columns:

- **Rank** — position in the exported order, starting at 1.
- **File** — the PDF file name.
- **Match %** — numeric percentage; blank for unreadable files.
- **Matched keywords** — semicolon-separated, with weights such as `python ×3`.
- **Missing keywords** — semicolon-separated.
- **Status** — OK, Scanned, Encrypted, or Error.
- **Path** — the full path to the source PDF.

The file is UTF-8 with a BOM so Excel opens accented names correctly. If you type
a file name without `.csv`, the app adds the extension.

## Settings and shortcuts

The app remembers your last folder, keywords, threshold, copy/move choice,
window size, and saved presets.

Shortcuts:

- `Cmd+O` — open a folder.
- `Cmd+E` — export the visible results as CSV.
- `Cmd+Return` — start processing, or cancel while scanning.
- **Help → User Guide** — open this guide in the app.

The **User Guide** button in the header does the same thing.

## Troubleshooting

**Start Processing is disabled.** Choose a folder that contains at least one
top-level PDF and enter at least one keyword.

**A file shows Scanned.** It is an image-only or nearly empty PDF. OCR is not
part of this version.

**A file shows Encrypted.** Remove the PDF password or export an unlocked copy,
then rescan.

**A file shows Error.** Confirm that it is a valid PDF. The rest of the scan
continues.

**No PDFs were found.** Check that you selected the folder itself, not a parent
folder. Only the top level is scanned.

**macOS asks for folder access.** Allow access to Desktop, Documents, or
Downloads the first time you scan those locations.

**The app is blocked on another Mac.** It is unsigned; right-click the app and
choose Open, or sign and notarize it for wider distribution.

**Excel shows odd characters.** The CSV is UTF-8 with a BOM and should open
directly. If you import manually, choose UTF-8.

## Privacy, performance, and limits

- Everything runs locally. Resume text is never uploaded.
- Extracted text is cached in memory by path and modification time, so changing
  keywords does not re-parse unchanged PDFs.
- Shortlisting copies by default; moving is opt-in.
- Only PDF files in the top level of the selected folder are processed.
- OCR, DOCX input, and Excel export are not included in this version.
- Tesseract is installed for future OCR work but is not used yet, and it is not
  bundled inside the macOS app.
"""

GUIDE_CSS = """
body {
    color: #E6E8EE;
    font-family: -apple-system, "SF Pro Text", sans-serif;
    font-size: 13px;
}
h1 { color: #E6E8EE; font-size: 23px; margin-bottom: 4px; }
h2 { color: #8F74FF; font-size: 16px; margin-top: 18px; }
h3 { color: #E6E8EE; font-size: 14px; margin-top: 12px; }
p, li { line-height: 1.45; }
a { color: #8F74FF; text-decoration: none; }
code { color: #CFC6FF; background-color: #1E222B; font-family: Menlo; }
pre { color: #E6E8EE; background-color: #1E222B; padding: 8px; }
blockquote { color: #8B93A5; }
"""


class UserGuideDialog(QDialog):
    """Modeless, scrollable guide rendered from USER_GUIDE.md content."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Resume Screener — User Guide")
        self.resize(780, 720)
        self.setModal(False)
        self.setSizeGripEnabled(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setFrameShape(QFrame.Shape.NoFrame)
        self.browser.document().setDefaultStyleSheet(GUIDE_CSS)
        self.browser.document().setDocumentMargin(12)
        self.browser.setMarkdown(GUIDE_MARKDOWN)
        layout.addWidget(self.browser, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
