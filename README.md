# Still Life Generator

A desktop GUI app that distorts images using AI image-to-image generation with [SD-Turbo](https://huggingface.co/stabilityai/sd-turbo). Runs entirely locally — no API keys, no cloud.

## Features

- Upload any image and generate a stylized "still life" version
- Adjustable change strength slider
- Download SD-Turbo model from HuggingFace on first launch (~1.5GB)
- Instant startup — model loads lazily on first use
- GPU (CUDA) and CPU support — auto-detected
- Choose output path or save to default `outputs/` folder

## Requirements

- **Python 3.10+**
- Pip dependencies (see below)

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/still-life-generator.git
cd still-life-generator

# Install dependencies
pip install torch diffusers transformers pillow huggingface_hub
```

Then launch:

- **Windows:** double-click `run.bat`
- **macOS / Linux:** `./run.sh` (or `python3 still_life_gui.py`)

On first launch, click **Download Model** to fetch SD-Turbo (~1.5GB). After that, the model is cached and the app opens instantly.

## Usage

1. Launch the app
2. If model not cached, click **Download Model**
3. Click **Upload Image** and select a JPG or PNG
4. Adjust the **Change** slider (lower = subtler, higher = more dramatic)
5. Click **Generate**
6. Save or browse the output

## Notes

- This app is intentionally simple — prompt is hardcoded to "uncanny" still life.
- All processing happens on your machine. No data is sent anywhere.
- Symlinks warning from HuggingFace Hub is safe to ignore on Windows (cache still works).
