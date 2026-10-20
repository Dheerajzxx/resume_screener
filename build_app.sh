#!/usr/bin/env bash
# Build a double-clickable macOS .app with PyInstaller.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x ".venv/bin/pyinstaller" ]]; then
  PYINSTALLER=".venv/bin/pyinstaller"
  PYTHON=".venv/bin/python"
elif command -v pyinstaller >/dev/null 2>&1; then
  PYINSTALLER="$(command -v pyinstaller)"
  PYTHON="$(command -v python3)"
else
  echo "PyInstaller not found. Run ./install.sh first." >&2
  exit 1
fi

VERSION="$("$PYTHON" -c 'from core import __version__; print(__version__)')"
APP="dist/Resume Screener.app"

ARGS=(
  --noconfirm
  --windowed
  --name "Resume Screener"
  --osx-bundle-identifier "com.resumescreener.app"
)
# PyMuPDF 2.0 imports its optional ONNX layout stack on `import pymupdf`.
# This app only extracts text, so leave that ~50 MB subsystem (and its
# resources) out of the bundle. The import is wrapped in try/except upstream.
ARGS+=(--exclude-module pymupdf.layout)
ARGS+=(--exclude-module pymupdf_layout)
ARGS+=(--exclude-module pymupdf4llm)
ARGS+=(--exclude-module onnxruntime)
if [[ -f "assets/icon.icns" ]]; then
  ARGS+=(--icon "assets/icon.icns")
fi

"$PYINSTALLER" "${ARGS[@]}" app.py

# PyInstaller leaves CFBundleShortVersionString at 0.0.0. Sync Finder/Get Info
# with the app version, then re-sign because editing Info.plist invalidates the
# ad-hoc signature PyInstaller applied.
/usr/bin/plutil -replace CFBundleShortVersionString -string "${VERSION}" "${APP}/Contents/Info.plist"
/usr/bin/plutil -replace CFBundleVersion -string "${VERSION}" "${APP}/Contents/Info.plist"
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "${APP}"
fi

echo "Built: ${APP} (version ${VERSION})"
