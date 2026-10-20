# Third-Party Notices

## License of the distributed binary

**The packaged `.app` and the release zip are an AGPL-3.0 combined work, not a
MIT-only distribution.** They include PyMuPDF, which is AGPL-3.0, so conveying
the binary conveys it under AGPL-3.0 (or under an Artifex commercial license if
you build with one and say so).

- The original Resume Screener source code stays MIT ([LICENSE](LICENSE)).
  MIT is permissive and compatible with inclusion in an AGPL-3.0 combined work;
  it does not relicense the binary.
- The full AGPL-3.0 text is attached to every release as
  `licenses/AGPL-3.0.txt` and ships in this repository under
  `licenses/AGPL-3.0.txt`, satisfying AGPL section 7.
- Corresponding source for the app code: this public repository,
  <https://github.com/Dheerajzxx/resume_screener>. Bundled PyMuPDF and
  Qt/PySide6 binaries are unmodified upstream builds; their sources are linked
  below.
- Qt/PySide6 remains LGPL-3.0: the libraries ship unmodified as dynamic
  libraries inside the bundle and remain replaceable, and `LGPL-3.0.txt` is
  attached to every release.
- Every release must state this binary license in its notes; see the
  release checklist at the bottom of this file.

## Repository source code

Resume Screener's original source code is licensed under the MIT License in
[LICENSE](LICENSE). Third-party components keep their own licenses. This summary
is provided for convenience, not as legal advice.

## Bundled in the macOS app

- **Python 3.12** — Python Software Foundation License 2.0.
  <https://docs.python.org/3/license.html>
- **PySide6 6.12 / Qt 6** — LGPL-3.0-only, GPL-2.0-only, or GPL-3.0-only,
  depending on the component and distribution terms.
  <https://www.qt.io/licensing/>
  <https://www.gnu.org/licenses/lgpl-3.0.html>
  The app bundles unmodified PySide6/Qt dynamic libraries. LGPL distribution
  requires preserving notices and allowing users to replace the libraries.
- **Shiboken6** — LGPL-3.0/GPL terms, as part of the PySide6 runtime.
  <https://pypi.org/project/shiboken6/>
- **PyMuPDF 2.0** — dual licensed under GNU AGPL-3.0 or an Artifex commercial
  license.
  <https://github.com/pymupdf/PyMuPDF>
  <https://www.gnu.org/licenses/agpl-3.0.html>
  <https://artifex.com/licensing/>
  **PyMuPDF is the key distribution constraint:** redistributing the bundled app
  with PyMuPDF requires complying with AGPL-3.0 (including source-availability
  obligations) or obtaining a commercial license from Artifex. The MIT license
  on this repository's original code does not replace those obligations.
- **NumPy 2.5** — BSD-3-Clause. A copy of the license is included in the
  `numpy-2.5.4.dist-info` metadata in the bundle.
  <https://numpy.org/doc/stable/license.html>
- **Pillow** — MIT-CMU (Historical Permission Notice and Disclaimer).
  <https://github.com/python-pillow/Pillow/blob/main/LICENSE>
- **PyYAML** — MIT.
  <https://github.com/yaml/pyyaml/blob/main/LICENSE>
- **psutil** — BSD-3-Clause.
  <https://github.com/giampaolo/psutil/blob/master/LICENSE>
- **PyInstaller bootloader** — GPL-2.0-or-later with the PyInstaller exception
  that permits building and distributing non-free programs.
  <https://pyinstaller.org/en/stable/license.html>

PyMuPDF's optional layout/ONNX modules (`pymupdf.layout`, `pymupdf_layout`,
`pymupdf4llm`, and `onnxruntime`) are intentionally excluded from the bundle by
`build_app.sh`.

## Installed for development or future use, not bundled

- **pytesseract** — Apache License 2.0.
  <https://github.com/madmaze/pytesseract>
- **Tesseract OCR** — Apache License 2.0. Installed by `install.sh` for future
  OCR work; it is not inside the `.app`.
  <https://github.com/tesseract-ocr/tesseract>

## Full license texts

The full AGPL-3.0 and LGPL-3.0 texts ship in the source repository under
`licenses/` and are attached to each GitHub release as `AGPL-3.0.txt` and
`LGPL-3.0.txt`.

The PyMuPDF and Qt/PySide6 project pages link the remaining notices and any
component-specific terms.

## Release checklist

Before distributing a binary, include the full license texts required by the
applicable licenses and review the obligations with legal counsel. In particular:

- Declare the binary as an **AGPL-3.0 combined work** in the release notes and
  in README, not as MIT-only.
- For AGPL-3.0, provide the corresponding source (this repository) and the AGPL
  text, or build against a PyMuPDF commercial license and say so explicitly.
- For LGPL-3.0, keep the Qt/PySide6 notices and make the libraries replaceable.
- Include this file and [LICENSE](LICENSE) with release downloads.

The GitHub source repository is intended to make the application source
available; it does not by itself grant a commercial PyMuPDF license.
