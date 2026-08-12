# Still Life Generator

A desktop GUI app inspired by the *Backrooms* "still life" concept: it progressively **erases a photo** — lighting effects, caustics, reflections, then objects — through iterative AI image-to-image passes, until only an empty room (or nothing) is left. Runs entirely locally with [SD-Turbo](https://huggingface.co/stabilityai/sd-turbo) — no API keys, no cloud.

## Features

- Upload any image and progressively erase its content (the "still life" effect)
- **Remove slider** — low = strip subtle detail (caustics, reflections, lighting); high = remove objects and eventually empty the scene (e.g. a pool loses its caustics, then its water)
- Download SD-Turbo model from HuggingFace on first launch (~1.5GB)
- Instant startup — model loads lazily on first use
- **Auto-detects your GPU (CUDA / Apple MPS) and falls back to CPU**
- **Device picker in the top-right corner** — switch between GPU and CPU anytime
- Native OS file explorer for picking/saving images (image previews on Linux)
- Choose output path or save to default `outputs/` folder

## Requirements

- **Python 3.10+** with `tkinter` (see platform notes below)
- About **2GB of free disk space** (model + dependencies)
- No internet required after the model is downloaded

## Installation

### Linux

```bash
# Debian/Ubuntu (tkinter is a separate package)
sudo apt install python3 python3-pip python3-venv python3-tk

./install_linux.sh
```

> Fedora: `sudo dnf install python3 python3-pip python3-tkinter`
> Arch: `sudo pacman -S python python-pip tk`

### macOS

```bash
./install_mac.sh
```

> If Python isn't installed, grab it from [python.org](https://python.org) (or `brew install python-tk@3.13`).

### Windows

Double-click `install_windows.bat` (or run it from a terminal).

> Install Python 3.10+ from [python.org](https://python.org) and tick **"Add python.exe to PATH"** during setup.

All three install scripts create an isolated virtual environment (`.venv`), **auto-detect an NVIDIA GPU**, and install the matching PyTorch build (CUDA if a GPU is present, otherwise CPU).

## Running

- **Windows:** double-click `run.bat`
- **macOS / Linux:** `./run.sh`

On first launch, click **Download Model** to fetch SD-Turbo (~1.5GB). After that, the model is cached and the app opens instantly.

## Usage

1. Launch the app
2. If model not cached, click **Download Model**
3. Click **Upload Image** and select a JPG or PNG
4. Set the **Remove** slider:
   - **low** (0.1–0.3) — strips subtle detail: caustics, reflections, small lighting effects
   - **medium** (0.4–0.6) — removes objects and large elements (e.g. water in a pool)
   - **high** (0.7–1.0) — erases nearly everything, ending as an empty, featureless room
5. Click **Generate** (runs several AI passes — the status bar shows progress)
6. Save or browse the output

## GPU acceleration (optional)

The app **auto-detects** available compute devices on launch and uses the fastest one (CUDA GPU > Apple MPS > CPU). You can override this anytime with the **Device** dropdown in the top-right corner of the window — switch between GPU and CPU on the fly.

- **Linux / Windows (NVIDIA):** the install scripts detect an NVIDIA GPU automatically and install the matching CUDA build of PyTorch. To install manually:

  ```bash
  python -m pip install torch --index-url https://download.pytorch.org/whl/cu130
  ```

  (Pick the correct CUDA version at [pytorch.org](https://pytorch.org) for your GPU/driver.)

- **macOS (Apple Silicon):** PyTorch's MPS backend is used automatically on Metal GPUs.

## Notes

- The prompt is fixed to the "empty still life" concept; the **Remove** slider only controls how much gets erased.
- All processing happens on your machine. No data is sent anywhere.
- Symlinks warning from HuggingFace Hub is safe to ignore on Windows (cache still works).
- If `./run.sh` gives a "Dependencies missing" error, run the install script for your platform first.

## Project layout

| File | Purpose |
|------|---------|
| `still_life_gui.py` | The app itself |
| `requirements.txt` | Python package list |
| `install_linux.sh` / `install_mac.sh` / `install_windows.bat` | One-shot dependency setup |
| `run.sh` / `run.bat` | Launch the app |
