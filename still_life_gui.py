import sys, os, shutil, subprocess, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# Keep the AI model inside this project folder (.huggingface/) instead of
# the user's home cache, so the app is self-contained next to run.sh.
os.environ.setdefault("HF_HOME", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".huggingface"))

MODEL_ID = "stabilityai/sd-turbo"

# Scene-agnostic dismorph gradient: each pass tries to *recreate* the same
# scene but gets it wrong, so the AI adds or strips content as intensity rises.
# Low = faithful but subtly wrong; mid = extra eyes/mouths, duplicated features
# and garbled text (letters get missing/swapped); high = everything stripped
# down to a bare empty room/cube. Text and objects look scrambled throughout.
DISMOORPH_PROMPTS = [
    "the same image, the same scene, the same subject, photorealistic, recreate it faithfully, subtle imperfections, readable text",
    "the same image, the same scene, photorealistic, slightly warped, imperfect edges, faint duplicated details, slightly misspelled text",
    "the same image, the same scene, recreated imperfectly, extra eyes and mouths, duplicated features, garbled text, missing letters, misspelled words",
    "the same scene, recreated badly, many extra eyes and mouths, multiplied objects, scrambled letters, jumbled words, gibberish text, melting, uncanny",
    "the same scene emptied, background stripped bare, distorted figure, empty walls, scrambled lettering, broken mangled objects, minimal, plain",
    "an empty room, bare walls, an empty cube, featureless, blank, nothing inside",
]
FLATTEN_PROMPT = "an empty room, an empty cube, bare walls, nothing inside, blank, featureless, minimal"

if sys.platform == "win32":
    FONT = "Segoe UI"
elif sys.platform == "darwin":
    FONT = "Helvetica"
else:
    FONT = "DejaVu Sans"

class EnhanceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Still Life Generator")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self.pipe = None
        self.input_image = None
        self.output_path = os.path.join(os.path.dirname(__file__), "outputs", "still_life_result.png")
        self._device = None
        self._dtype = None
        self._devices = None
        self.model_ready = False
        self._animating = False

        self.build_ui()
        self.center_window()
        self.root.after(200, self.check_model)
        self.root.mainloop()

    @property
    def devices(self):
        if self._devices is None:
            self._devices = self._detect_devices()
        return self._devices

    @property
    def device(self):
        if self._device is None:
            self._device = self.devices[0]
        return self._device

    @device.setter
    def device(self, value):
        value = str(value).lower()
        if value not in self.devices:
            return
        if value == self._device:
            return
        self._device = value
        self._dtype = None
        if self.pipe is not None:
            self.pipe = None
            self.set_status("Device changed - model will reload on next Generate.")

    @property
    def dtype(self):
        if self._dtype is None:
            import torch
            self._dtype = torch.float16 if self.device == "cuda" else torch.float32
        return self._dtype

    def _detect_devices(self):
        devices = []
        try:
            import torch
            if torch.cuda.is_available():
                devices.append("cuda")
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                devices.append("mps")
        except Exception:
            pass
        devices.append("cpu")
        return devices

    def _device_desc(self, dev):
        if dev == "cuda":
            import torch
            try:
                return torch.cuda.get_device_name(0)
            except Exception:
                return "NVIDIA GPU"
        if dev == "mps":
            return "Apple GPU"
        return "CPU"

    def _update_device_label(self):
        desc = self._device_desc(self.device)
        self.device_label.configure(text=desc)
        self.device_label.configure(fg="#76ff03" if self.device != "cpu" else "#888")

    def center_window(self):
        self.root.update_idletasks()
        w, h = 820, 710
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{sw//2-w//2}+{sh//2-h//2}")

    def build_ui(self):
        main = tk.Frame(self.root, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=20, pady=15)

        header = tk.Frame(main, bg="#1a1a2e")
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Still Life Generator", font=(FONT, 22, "bold"),
                bg="#1a1a2e", fg="#e94560").pack(side="left")

        devbox = tk.Frame(header, bg="#16213e", padx=10, pady=4)
        devbox.pack(side="right")
        tk.Label(devbox, text="Device:", font=(FONT, 9, "bold"), bg="#16213e", fg="#ccc").pack(side="left")
        self.device_combo = ttk.Combobox(devbox, state="readonly", width=5, font=(FONT, 9))
        self.device_combo.pack(side="left", padx=(6, 2))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_change)
        self.device_label = tk.Label(devbox, text="", font=(FONT, 8), bg="#16213e", fg="#888")
        self.device_label.pack(side="left", padx=(6, 0))

        self.device_combo["values"] = [d.upper() for d in self.devices]
        self.device_combo.current(self.devices.index(self.device))
        self._update_device_label()

        btn_frame = tk.Frame(main, bg="#1a1a2e")
        btn_frame.pack(pady=10)

        self.dl_btn = tk.Button(btn_frame, text="Download Model", bg="#0f3460", fg="white",
                                font=(FONT, 11, "bold"), relief="flat",
                                command=self.download_model, cursor="hand2", padx=15)
        self.dl_btn.pack(side="left", padx=5, ipady=4)
        self.load_btn = tk.Button(btn_frame, text="Upload Image", bg="#0f3460", fg="white",
                                  font=(FONT, 11, "bold"), relief="flat",
                                  command=self.upload_image, cursor="hand2", state="disabled", padx=15)
        self.load_btn.pack(side="left", padx=5, ipady=4)
        self.gen_btn = tk.Button(btn_frame, text="Generate", bg="#e94560", fg="white",
                                 font=(FONT, 11, "bold"), relief="flat",
                                 command=self.run_generate, cursor="hand2", state="disabled", padx=15)
        self.gen_btn.pack(side="left", padx=5, ipady=4)

        ctrl_frame = tk.Frame(main, bg="#1a1a2e")
        ctrl_frame.pack(fill="x", pady=(5, 0))

        sframe = tk.Frame(ctrl_frame, bg="#1a1a2e")
        sframe.pack(fill="x", pady=(5, 0))
        tk.Label(sframe, text="Remove:", font=(FONT, 10), bg="#1a1a2e", fg="#ccc").pack(side="left")
        self.strength_var = tk.DoubleVar(value=0.5)
        self.strength_slider = tk.Scale(sframe, from_=0.1, to=1.0, resolution=0.01, orient="horizontal",
                                        variable=self.strength_var, bg="#1a1a2e", fg="#ccc",
                                        highlightthickness=0, troughcolor="#16213e",
                                        activebackground="#e94560", length=280, font=(FONT, 8))
        self.strength_slider.pack(side="left", padx=10)
        self.strength_value = tk.Label(sframe, text="0.50", font=(FONT, 10, "bold"),
                                       bg="#1a1a2e", fg="#e94560", width=5)
        self.strength_value.pack(side="left", padx=(0, 10))
        self.strength_slider.configure(command=self._on_strength_change)
        tk.Label(sframe, text="low = subtle glitch | high = empty room", font=(FONT, 8),
                 bg="#1a1a2e", fg="#666").pack(side="left")

        oframe = tk.Frame(ctrl_frame, bg="#1a1a2e")
        oframe.pack(fill="x", pady=(5, 0))
        tk.Label(oframe, text="Save to:", font=(FONT, 10), bg="#1a1a2e", fg="#ccc").pack(side="left")
        self.out_path_label = tk.Label(oframe, text=self.output_path, font=(FONT, 8),
                                       bg="#16213e", fg="#888", anchor="w", padx=6, pady=3)
        self.out_path_label.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(oframe, text="Browse", bg="#0f3460", fg="white", font=(FONT, 9),
                  relief="flat", command=self.choose_output, cursor="hand2", padx=8).pack(side="left")

        self.progress_bar = ttk.Progressbar(main, length=780, mode="determinate", value=0)
        self.progress_bar.pack(pady=(5, 0))

        self.status = tk.Label(main, text="Checking model...", font=(FONT, 10), bg="#1a1a2e", fg="#888")
        self.status.pack()
        self.progress_label = tk.Label(main, text="", font=(FONT, 9), bg="#1a1a2e", fg="#555")
        self.progress_label.pack()

        img_frame = tk.Frame(main, bg="#1a1a2e")
        img_frame.pack(fill="both", expand=True, pady=5)
        self.orig_canvas = tk.Canvas(img_frame, bg="#16213e", highlightthickness=0, width=370, height=370)
        self.orig_canvas.pack(side="left", padx=5, fill="both", expand=True)
        self.orig_canvas.create_text(185, 185, text="Original", fill="#555", font=(FONT, 11), tags="p")
        self.gen_canvas = tk.Canvas(img_frame, bg="#16213e", highlightthickness=0, width=370, height=370)
        self.gen_canvas.pack(side="right", padx=5, fill="both", expand=True)
        self.gen_canvas.create_text(185, 185, text="Generated", fill="#555", font=(FONT, 11), tags="p")

    def _on_strength_change(self, val):
        try:
            v = float(val)
        except Exception:
            v = self.strength_var.get()
        self.strength_var.set(v)
        self.strength_value.configure(text=f"{v:.2f}")

    def _on_device_change(self, event=None):
        self.device = self.device_combo.get().lower()
        self._update_device_label()
        self.set_status(f"Device set to {self.device.upper()}.")

    def check_model(self):
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(MODEL_ID, "model_index.json", local_files_only=True)
            self.model_ready = True
            self.set_status("Model ready! Upload an image.", f"Device: {self.device.upper()}")
            self.load_btn.configure(state="normal")
            self.dl_btn.pack_forget()
        except Exception:
            self.set_status("Click 'Download Model' (~1.5GB).", f"Device: {self.device.upper()}")
        self._update_device_label()

    def set_status(self, text, prog=""):
        self.status.configure(text=text)
        self.progress_label.configure(text=prog)
        self.root.update()

    def choose_output(self):
        path = self._ask_save()
        if path:
            self.output_path = path
            self.out_path_label.configure(text=path)

    def _ask_open(self):
        """Open the OS-native file explorer (with image thumbnails) where possible."""
        if sys.platform.startswith("linux"):
            exe = shutil.which("zenity") or shutil.which("kdialog")
            if exe:
                try:
                    if "zenity" in exe:
                        out = subprocess.run(
                            [exe, "--file-selection", "--title", "Select an image",
                             "--file-filter", "Images | *.jpg *.jpeg *.png *.bmp *.webp *.gif",
                             "--file-filter", "All files | *"],
                            capture_output=True, text=True, timeout=600)
                    else:
                        out = subprocess.run(
                            [exe, "--getopenfilename", os.path.expanduser("~"),
                             "Images (*.jpg *.jpeg *.png *.bmp *.webp *.gif)"],
                            capture_output=True, text=True, timeout=600)
                    if out.returncode == 0:
                        return out.stdout.strip() or None
                    return None
                except Exception:
                    pass
        return filedialog.askopenfilename(parent=self.root,
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp *.gif"), ("All Files", "*.*")])

    def _ask_save(self):
        """Open the OS-native save dialog where possible."""
        default = self.output_path
        if sys.platform.startswith("linux"):
            exe = shutil.which("zenity") or shutil.which("kdialog")
            if exe:
                try:
                    if "zenity" in exe:
                        out = subprocess.run(
                            [exe, "--file-selection", "--save", "--title", "Save image",
                             "--filename", default, "--file-filter", "PNG | *.png"],
                            capture_output=True, text=True, timeout=600)
                    else:
                        out = subprocess.run(
                            [exe, "--getsavefilename", default, "PNG (*.png)"],
                            capture_output=True, text=True, timeout=600)
                    if out.returncode == 0:
                        p = out.stdout.strip()
                        if p and not p.lower().endswith(".png"):
                            p += ".png"
                        return p or None
                    return None
                except Exception:
                    pass
        return filedialog.asksaveasfilename(parent=self.root, defaultextension=".png",
            filetypes=[("PNG", "*.png")], initialfile=os.path.basename(default))

    def download_model(self):
        if not messagebox.askyesno("Download Model", "Download SD-Turbo (~1.5GB)?\nMay take 10-30 minutes. Continue?"):
            return
        self.dl_btn.configure(state="disabled", text="Downloading...")
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        from huggingface_hub import hf_hub_download, HfApi
        try:
            api = HfApi()
            siblings = [s for s in api.model_info(MODEL_ID).siblings
                        if not s.rfilename.endswith(".gitattributes")
                        and not (s.rfilename.endswith(".safetensors") and "/" not in s.rfilename)]
            total = len(siblings)
            for i, s in enumerate(siblings):
                self.root.after(0, lambda f=s.rfilename, n=i+1, t=total: (
                    self.progress_bar.configure(value=int(n/t*100)),
                    self.set_status(f"Downloading ({n}/{t})", os.path.basename(f))
                ))
                hf_hub_download(MODEL_ID, s.rfilename, resume_download=True)
            self.model_ready = True
            self.root.after(0, lambda: (
                self.progress_bar.configure(value=100), self.load_btn.configure(state="normal"),
                self.dl_btn.pack_forget(),
                self.set_status("Model ready! Upload an image.", f"Device: {self.device.upper()}")
            ))
        except Exception as e:
            self.root.after(0, lambda: (
                self.set_status(f"Download failed: {e}"),
                self.dl_btn.configure(state="normal", text="Download Model")
            ))

    def upload_image(self):
        path = self._ask_open()
        if not path: return
        self.input_image = Image.open(path).convert("RGB")
        self.show_on_canvas(self.orig_canvas, self.input_image, "Original")
        self.gen_btn.configure(state="normal")
        self.gen_canvas.delete("all")
        self.gen_canvas.create_text(185, 185, text="Generated", fill="#555", font=(FONT, 11), tags="p")
        self.set_status(f"Loaded: {os.path.basename(path)}")

    def show_on_canvas(self, canvas, img, label):
        canvas.delete("all")
        self.root.update_idletasks()
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 50: cw = 370
        if ch < 50: ch = 370
        copy = img.copy()
        copy.thumbnail((cw - 20, ch - 20), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(copy)
        canvas.image = photo
        canvas.create_image(cw // 2, ch // 2, image=photo)
        canvas.create_text(cw // 2, 20, text=label, fill="#e94560", font=(FONT, 10, "bold"))

    def _dismorph_plan(self, intensity):
        # Remap so the slider's full 1.0 equals the old 0.7 max effect.
        # This keeps the output recognizable and gives finer control
        # across the whole range instead of blowing up past 0.7.
        eff = intensity * 0.7
        passes = max(1, int(round(eff * 8)))
        strength = 0.35 + (eff ** 1.2) * 0.45
        if eff >= 0.5:
            flatten = min(0.8, 0.5 + eff * 0.3)
        elif eff >= 0.35:
            flatten = 0.3 + eff * 0.35
        else:
            flatten = None
        return passes, strength, flatten

    def run_generate(self):
        if self.input_image is None: return
        self.gen_btn.configure(state="disabled", text="Generating...")
        self.progress_bar["mode"] = "determinate"
        self.progress_bar.configure(value=0)
        self.set_status("Dismorphing...", "recreating the scene, badly (iterative passes)")
        self._animating = True
        self._animate_status()
        threading.Thread(target=self._generate_thread, daemon=True).start()

    def _animate_status(self, idx=0):
        if not self._animating: return
        colors = ["#888", "#aaa", "#ccc", "#aaa"]
        self.status.configure(fg=colors[idx % len(colors)])
        self.root.after(400, lambda: self._animate_status(idx + 1))

    def _generate_thread(self):
        from diffusers import AutoPipelineForImage2Image
        try:
            if self.pipe is None:
                self.root.after(0, lambda: self.set_status("Loading model into memory..."))
                self.pipe = AutoPipelineForImage2Image.from_pretrained(
                    MODEL_ID, torch_dtype=self.dtype,
                    safety_checker=None, requires_safety_checker=False
                )
                self.pipe.to(self.device)
                if self.device == "cuda": self.pipe.enable_attention_slicing()

            intensity = self.strength_var.get()
            passes, strength, flatten_strength = self._dismorph_plan(intensity)
            total = passes + (1 if flatten_strength is not None else 0)

            init = self.input_image.copy()
            w, h = init.size
            ratio = 512 / max(w, h)
            nw, nh = max(64, int((w * ratio) / 64) * 64), max(64, int((h * ratio) / 64) * 64)
            current = init.resize((nw, nh), Image.Resampling.LANCZOS)

            self.root.after(0, lambda: (
                self.progress_bar.stop(),
                self.progress_bar.configure(mode="determinate", value=0)
            ))

            for i in range(passes):
                depth = i / passes
                idx = min(len(DISMOORPH_PROMPTS) - 1, int(depth * len(DISMOORPH_PROMPTS)))
                self.root.after(0, lambda i=i, idx=idx, total=total: (
                    self.progress_bar.configure(value=int(i / total * 100)),
                    self.set_status(f"Dismorph pass {i + 1}/{total}", DISMOORPH_PROMPTS[idx][:55])
                ))
                current = self.pipe(DISMOORPH_PROMPTS[idx], image=current, strength=strength,
                                    num_inference_steps=8, guidance_scale=0.0).images[0]

            if flatten_strength is not None:
                self.root.after(0, lambda total=total: (
                    self.progress_bar.configure(value=int(passes / total * 100)),
                    self.set_status(f"Corrupting (pass {total}/{total})", "warping it further")
                ))
                current = self.pipe(FLATTEN_PROMPT, image=current, strength=flatten_strength,
                                    num_inference_steps=8, guidance_scale=0.0).images[0]

            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            current.save(self.output_path)
            self.root.after(0, lambda: self._show_result(current, self.output_path))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: messagebox.showerror("Error", err))
            self.root.after(0, lambda: self.set_status(f"Error: {err}"))
        finally:
            self._animating = False
            self.root.after(0, lambda: (
                self.progress_bar.stop(), self.progress_bar.configure(mode="determinate", value=100),
                self.gen_btn.configure(state="normal", text="Generate"), self.status.configure(fg="#888")
            ))

    def _show_result(self, img, path):
        self.show_on_canvas(self.gen_canvas, img, "Generated")
        self.set_status(f"Done! Saved to {os.path.basename(path)}")

if __name__ == "__main__":
    EnhanceApp()