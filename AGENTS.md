# Project knowledge

This file gives Freebuff context about your project: goals, commands, conventions, and gotchas.
See `knowledge.md` for the full implementation notes and `GOAL.md` for the original spec.

## Quickstart
- Setup: `./install.sh` (idempotent; macOS, Python 3.12)
- Dev: `./run.sh`
- Test: `.venv/bin/python -m pytest`
- Package: `./build_app.sh` -> `dist/Resume Screener.app`

## Architecture
- Key directories: `core/` (Qt-free PDF extraction, matching, shortlisting), `ui/` (PySide6 window, worker, table model, delegates, theme), `tests/`.
- Data flow: folder scan -> `ScanWorker` on a `QThread` -> `extract_text_cached` -> `score` -> `ResultRow` -> table model/proxy -> shortlist.

## Conventions
- Formatting/linting: PEP 8, 4 spaces; no linter is configured.
- Patterns to follow: keep `core/` free of Qt; use theme tokens from `ui/theme.py`; emit background work through signals; parse keywords into `Keyword(text, weight)` and store presets through `PresetStore`.
- Things to avoid: calling `str.format` on QSS (literal braces); re-adding PyMuPDF's optional ONNX layout modules to the bundle; matching keywords without whole-word boundaries.
- User guide: `USER_GUIDE.md` is the source; `ui/user_guide.py` embeds it for the in-app dialog. Keep the two in sync (`tests/test_user_guide.py` enforces this).
- Release: bump `core.__version__` and `CHANGELOG.md`, then push a matching `vX.Y.Z` tag; `.github/workflows/release.yml` builds the arm64 zip on `macos-26` and publishes it with `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `licenses/` texts.
- Licensing: repo code is MIT; the distributed `.app`/zip is an **AGPL-3.0 combined work** (bundles PyMuPDF; PySide6/Qt stays LGPL). Release notes and README must say so — never call the binary MIT-only. Read `THIRD_PARTY_NOTICES.md` before distributing binaries.
