#!/usr/bin/env bash
# Build a double-clickable macOS .app with PyInstaller.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x ".venv/bin/pyinstaller" ]]; then
  PYINSTALLER=".venv/bin/pyinstaller"
elif command -v pyinstaller >/dev/null 2>&1; then
  PYINSTALLER="$(command -v pyinstaller)"
else
  echo "PyInstaller not found. Run ./install.sh first." >&2
  exit 1
fi

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
echo "Built: dist/Resume Screener.app"
