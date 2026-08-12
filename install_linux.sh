#!/usr/bin/env bash
# Install dependencies for Still Life Generator on Linux.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

echo "==> Checking Python..."
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "ERROR: '$PY' not found. Install Python 3.10+ first, e.g.:"
    echo "  Debian/Ubuntu: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    exit 1
fi
"$PY" --version

echo "==> Checking tkinter (GUI toolkit)..."
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: tkinter is missing. Install it, e.g.:"
    echo "  Debian/Ubuntu: sudo apt install python3-tk"
    echo "  Fedora:        sudo dnf install python3-tkinter"
    echo "  Arch:          sudo pacman -S tk"
    exit 1
fi

echo "==> Detecting GPU..."
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    echo "    NVIDIA GPU found: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
    DEFAULT_INDEX="https://download.pytorch.org/whl/cu130"
else
    echo "    No NVIDIA GPU detected - installing CPU build."
    DEFAULT_INDEX="https://download.pytorch.org/whl/cpu"
fi
# Override with:  TORCH_INDEX=<url> ./install_linux.sh
TORCH_INDEX="${TORCH_INDEX:-$DEFAULT_INDEX}"
echo "    PyTorch source: $TORCH_INDEX"

echo "==> Creating virtual environment (.venv)..."
if [ ! -x ".venv/bin/python" ]; then
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate

echo "==> Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install torch --index-url "$TORCH_INDEX"
python -m pip install -r requirements.txt

echo
echo "Done! Launch the app with:  ./run.sh"
echo
if [[ "$TORCH_INDEX" == *cpu* ]]; then
    echo "NOTE: No GPU was detected. If you add one later, re-run this script"
    echo "      or set TORCH_INDEX=https://download.pytorch.org/whl/cu130"
else
    echo "NOTE: CUDA build installed. The app auto-detects it and shows the GPU"
    echo "      in the top-right corner of the window (GPU / CPU dropdown)."
fi
