# Contributing to Resume Screener

Thanks for helping improve Resume Screener. This is a macOS desktop app built
with Python 3.12, PySide6, and PyMuPDF.

## Development setup

Requirements: macOS on Apple silicon, Xcode Command Line Tools, Homebrew, and
Python 3.12.

```bash
./install.sh
source .venv/bin/activate
pytest
./run.sh
```

`install.sh` is idempotent and installs only missing prerequisites/packages.

If you prefer to set up manually:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Before opening a pull request

- Run the full test suite: `.venv/bin/python -m pytest`.
- Run `bash -n install.sh run.sh build_app.sh`.
- Run `python -m compileall -q app.py core ui tests`.
- Update `README.md`, `USER_GUIDE.md`, or `knowledge.md` when behavior changes.
- If you change `USER_GUIDE.md`, update `GUIDE_MARKDOWN` in `ui/user_guide.py`;
  `tests/test_user_guide.py` enforces that they match.
- If you change UI text, keyboard shortcuts, or dialogs, add or update a
  headless test where practical.

The macOS app is ad-hoc signed but not Developer ID-signed or notarized.
Packaging changes should be checked with `./build_app.sh` and a launch of
`dist/Resume Screener.app`.

## Code layout and conventions

- `core/` contains Qt-free logic (PDF extraction, matching, shortlisting, CSV
  export). Do not import Qt or PySide6 there.
- `ui/` contains PySide6 widgets, the table model/delegates, presets, theme,
  and the in-app user guide.
- `tests/` covers core behavior plus headless UI flows. UI tests use
  `QT_QPA_PLATFORM=offscreen`.
- Follow PEP 8 with 4-space indentation and keep functions focused.
- Use the theme tokens in `ui/theme.py` rather than adding ad-hoc colors.
- Never call `str.format` on the QSS string: it contains literal braces.
- Keep long-running PDF work on the `ScanWorker` thread.

## Adding dependencies

Add runtime/test packages to `requirements.txt` with a sensible upper bound,
then install and run the tests. Avoid adding a dependency for something the
standard library already handles well.

## Release process

0. For the first release, create the GitHub repository and push `main`:

   ```bash
   git init
   git checkout -b main
   git add .
   git commit -m "Initial release"
   gh repo create <owner>/resume-screener --public --source=. --remote=origin --push
   ```

1. Update `__version__` in `core/__init__.py` and `CHANGELOG.md`.
2. Run the full test suite and `./build_app.sh`.
3. Review [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); keep the bundled
   dependency list and `licenses/` texts accurate if dependencies change.
4. Commit the version bump, push the branch, and tag:

   ```bash
   git add -A
   git commit -m "Release v1.0.0"
   git push origin HEAD
   git tag v1.0.0
   git push origin v1.0.0
   ```

5. The **Release** GitHub Actions workflow verifies the tag matches
   `__version__`, builds an arm64 `.app`, writes SHA-256 checksums, and creates
   the GitHub release with the zip, license, notices, and full license texts.

## License

By contributing, you agree that your contributions are licensed under the MIT
License in [LICENSE](LICENSE) for the original project code. Distributed
binaries are an **AGPL-3.0 combined work** because they bundle PyMuPDF; they
must not be described as MIT-only. Bundled third-party components have their
own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), especially the
PyMuPDF AGPL/commercial and PySide6 LGPL requirements.
