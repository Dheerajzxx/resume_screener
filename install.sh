#!/usr/bin/env bash
# install.sh - idempotent installer for Resume Screener (macOS, Apple silicon)
set -euo pipefail

GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RED="\033[0;31m"; NC="\033[0m"
ok()   { echo -e "${GREEN}[ok]${NC}   $1 (already installed, skipping)"; }
inst() { echo -e "${YELLOW}[install]${NC} $1"; }
die()  { echo -e "${RED}[error]${NC} $1"; exit 1; }

PY_VERSION="3.12"
VENV_DIR=".venv"
PIP_PACKAGES=("PySide6" "PyMuPDF" "pytesseract" "pyinstaller" "pytest")

cd "$(dirname "$0")"

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
PYTHON_BIN="$(command -v "python${PY_VERSION}")"

# 4. Tesseract (optional OCR engine, used by the planned v2 OCR support)
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
for mod in ("PySide6", "pymupdf", "pytesseract", "pytest"):
    importlib.import_module(mod)
print("All Python modules import correctly.")
EOF

echo -e "\n${GREEN}Setup complete.${NC} Start the app with: ./run.sh"
