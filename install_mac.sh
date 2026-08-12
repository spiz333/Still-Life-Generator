#!/usr/bin/env bash
# Install dependencies for Still Life Generator on macOS.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

echo "==> Checking Python..."
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "ERROR: '$PY' not found. Install Python 3.10+ from https://python.org"
    echo "       or with Homebrew:  brew install python-tk@3.13"
    exit 1
fi
"$PY" --version

echo "==> Checking tkinter (GUI toolkit)..."
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: tkinter is missing. On macOS, use the python.org installer,"
    echo "       or install with Homebrew:  brew install python-tk@3.13"
    exit 1
fi

echo "==> Creating virtual environment (.venv)..."
if [ ! -x ".venv/bin/python" ]; then
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate

echo "==> Installing Python packages (Apple Silicon / CPU build of PyTorch, ~200MB)..."
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt

echo
echo "Done! Launch the app with:  ./run.sh"
echo
echo "NOTE: Apple Silicon Macs automatically use the faster MPS backend."
echo "      The app auto-detects it and shows the device in the top-right"
echo "      corner of the window (GPU / CPU dropdown)."
