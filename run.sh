#!/bin/bash
cd "$(dirname "$0")"
mkdir -p outputs
python3 still_life_gui.py 2>/dev/null || python still_life_gui.py
