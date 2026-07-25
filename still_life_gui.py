import sys, os, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

MODEL_ID = "stabilityai/sd-turbo"

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
        self.model_ready = False
        self._animating = False

        self.build_ui()
        self.center_window()
        self.root.after(200, self.check_model)
        self.root.mainloop()

    @property
    def device(self):
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    @property
    def dtype(self):
        if self._dtype is None:
            import torch
            self._dtype = torch.float16 if self.device == "cuda" else torch.float32
        return self._dtype

    def center_window(self):
        self.root.update_idletasks()
        w, h = 820, 710
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{sw//2-w//2}+{sh//2-h//2}")

    def build_ui(self):
        main = tk.Frame(self.root, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(main, text="Still Life Generator", font=("Segoe UI", 22, "bold"),
                bg="#1a1a2e", fg="#e94560").pack()

        btn_frame = tk.Frame(main, bg="#1a1a2e")
        btn_frame.pack(pady=10)

        self.dl_btn = tk.Button(btn_frame, text="Download Model", bg="#0f3460", fg="white",
                                font=("Segoe UI", 11, "bold"), relief="flat",
                                command=self.download_model, cursor="hand2", padx=15)
        self.dl_btn.pack(side="left", padx=5, ipady=4)
        self.load_btn = tk.Button(btn_frame, text="Upload Image", bg="#0f3460", fg="white",
                                  font=("Segoe UI", 11, "bold"), relief="flat",
                                  command=self.upload_image, cursor="hand2", state="disabled", padx=15)
        self.load_btn.pack(side="left", padx=5, ipady=4)
        self.gen_btn = tk.Button(btn_frame, text="Generate", bg="#e94560", fg="white",
                                 font=("Segoe UI", 11, "bold"), relief="flat",
                                 command=self.run_generate, cursor="hand2", state="disabled", padx=15)
        self.gen_btn.pack(side="left", padx=5, ipady=4)
        self.device_label = tk.Label(btn_frame, text="", font=("Segoe UI", 8), bg="#1a1a2e", fg="#666")
        self.device_label.pack(side="left", padx=10)

        ctrl_frame = tk.Frame(main, bg="#1a1a2e")
        ctrl_frame.pack(fill="x", pady=(5, 0))

        sframe = tk.Frame(ctrl_frame, bg="#1a1a2e")
        sframe.pack(fill="x", pady=(5, 0))
        tk.Label(sframe, text="Change:", font=("Segoe UI", 10), bg="#1a1a2e", fg="#ccc").pack(side="left")
        self.strength_var = tk.DoubleVar(value=0.35)
        self.strength_slider = tk.Scale(sframe, from_=0.1, to=0.7, resolution=0.05, orient="horizontal",
                                        variable=self.strength_var, bg="#1a1a2e", fg="#ccc",
                                        highlightthickness=0, troughcolor="#16213e",
                                        activebackground="#e94560", length=280, font=("Segoe UI", 8))
        self.strength_slider.pack(side="left", padx=10)
        tk.Label(sframe, text="lower=subtler", font=("Segoe UI", 8), bg="#1a1a2e", fg="#666").pack(side="left")

        oframe = tk.Frame(ctrl_frame, bg="#1a1a2e")
        oframe.pack(fill="x", pady=(5, 0))
        tk.Label(oframe, text="Save to:", font=("Segoe UI", 10), bg="#1a1a2e", fg="#ccc").pack(side="left")
        self.out_path_label = tk.Label(oframe, text=self.output_path, font=("Segoe UI", 8),
                                       bg="#16213e", fg="#888", anchor="w", padx=6, pady=3)
        self.out_path_label.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(oframe, text="Browse", bg="#0f3460", fg="white", font=("Segoe UI", 9),
                  relief="flat", command=self.choose_output, cursor="hand2", padx=8).pack(side="left")

        self.progress_bar = ttk.Progressbar(main, length=780, mode="determinate", value=0)
        self.progress_bar.pack(pady=(5, 0))

        self.status = tk.Label(main, text="Checking model...", font=("Segoe UI", 10), bg="#1a1a2e", fg="#888")
        self.status.pack()
        self.progress_label = tk.Label(main, text="", font=("Segoe UI", 9), bg="#1a1a2e", fg="#555")
        self.progress_label.pack()

        img_frame = tk.Frame(main, bg="#1a1a2e")
        img_frame.pack(fill="both", expand=True, pady=5)
        self.orig_canvas = tk.Canvas(img_frame, bg="#16213e", highlightthickness=0, width=370, height=370)
        self.orig_canvas.pack(side="left", padx=5, fill="both", expand=True)
        self.orig_canvas.create_text(185, 185, text="Original", fill="#555", font=("Segoe UI", 11), tags="p")
        self.gen_canvas = tk.Canvas(img_frame, bg="#16213e", highlightthickness=0, width=370, height=370)
        self.gen_canvas.pack(side="right", padx=5, fill="both", expand=True)
        self.gen_canvas.create_text(185, 185, text="Generated", fill="#555", font=("Segoe UI", 11), tags="p")

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
        self.device_label.configure(text=self.device.upper())

    def set_status(self, text, prog=""):
        self.status.configure(text=text)
        self.progress_label.configure(text=prog)
        self.root.update()

    def choose_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")],
                                            initialfile="still_life_result.png")
        if path:
            self.output_path = path
            self.out_path_label.configure(text=path)

    def download_model(self):
        if not messagebox.askyesno("Download Model", "Download SD-Turbo (~1.5GB)?\nMay take 10-30 minutes. Continue?"):
            return
        self.dl_btn.configure(state="disabled", text="Downloading...")
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        from huggingface_hub import hf_hub_download, HfApi
        try:
            api = HfApi()
            siblings = [s for s in api.model_info(MODEL_ID).siblings if not s.rfilename.endswith(".gitattributes")]
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
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if not path: return
        self.input_image = Image.open(path).convert("RGB")
        self.show_on_canvas(self.orig_canvas, self.input_image, "Original")
        self.gen_btn.configure(state="normal")
        self.gen_canvas.delete("all")
        self.gen_canvas.create_text(185, 185, text="Generated", fill="#555", font=("Segoe UI", 11), tags="p")
        self.set_status(f"Loaded: {os.path.basename(path)}")

    def show_on_canvas(self, canvas, img, label):
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 50: cw = 370
        if ch < 50: ch = 370
        copy = img.copy()
        copy.thumbnail((cw - 20, ch - 20), Image.LANCZOS)
        photo = ImageTk.PhotoImage(copy)
        canvas.image = photo
        canvas.create_image(cw // 2, ch // 2, image=photo)
        canvas.create_text(cw // 2, 20, text=label, fill="#e94560", font=("Segoe UI", 10, "bold"))

    def run_generate(self):
        if self.input_image is None: return
        self.gen_btn.configure(state="disabled", text="Generating...")
        self.progress_bar["mode"] = "indeterminate"
        self.progress_bar.start(10)
        self.set_status("Generating...", "SD-Turbo (10 steps)...")
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

            strength = self.strength_var.get()
            init = self.input_image.copy()
            w, h = init.size
            ratio = 512 / max(w, h)
            nw, nh = max(64, int((w * ratio) / 64) * 64), max(64, int((h * ratio) / 64) * 64)
            init = init.resize((nw, nh), Image.LANCZOS)

            result = self.pipe(prompt="uncanny", image=init, strength=strength,
                               num_inference_steps=10, guidance_scale=0.0).images[0]

            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            result.save(self.output_path)
            self.root.after(0, lambda: self._show_result(result, self.output_path))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: messagebox.showerror("Error", err))
            self.root.after(0, lambda: self.set_status(f"Error: {err}"))
        finally:
            self._animating = False
            self.root.after(0, lambda: (
                self.progress_bar.stop(), self.progress_bar.configure(mode="determinate", value=0),
                self.gen_btn.configure(state="normal", text="Generate"), self.status.configure(fg="#888")
            ))

    def _show_result(self, img, path):
        self.show_on_canvas(self.gen_canvas, img, "Generated")
        self.set_status(f"Done! Saved to {os.path.basename(path)}")

if __name__ == "__main__":
    EnhanceApp()