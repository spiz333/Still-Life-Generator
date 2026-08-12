#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p outputs

# Keep the AI model in this project's .huggingface/ folder.
export HF_HOME="$(pwd)/.huggingface"

# Find a Python interpreter that already has the required dependencies installed.
# Prefer one that also has GPU (CUDA) support; otherwise any working one.
# Prefer the project venv, then fall back to system python3 / python.
PY=""
FALLBACK=""
for cand in .venv/bin/python python3 python; do
    if command -v "$cand" >/dev/null 2>&1 \
        && "$cand" -c "import diffusers, torch, PIL, tkinter" >/dev/null 2>&1; then
        if "$cand" -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
        [ -z "$FALLBACK" ] && FALLBACK="$cand"
    fi
done
[ -z "$PY" ] && PY="$FALLBACK"

if [ -z "$PY" ]; then
    cat >&2 <<'EOF'
ERROR: Dependencies are missing.

Install them first (one time only), then run this script again:
  Linux:     ./install_linux.sh
  macOS:     ./install_mac.sh
  Windows:   install_windows.bat

Note: if you installed Python dependencies globally, this script will
automatically pick them up and the venv (.venv) can be deleted.
EOF
    exit 1
fi

exec "$PY" still_life_gui.py
