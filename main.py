import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import traceback
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image


class WebpConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch WebP to JPG Converter")
        self.root.geometry("600x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.delete_source = tk.BooleanVar(value=False)
        self.include_jpg = tk.BooleanVar(value=False)
        self.is_running = False

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6, relief="flat", background="#6c63ff", foreground="white", font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#857dff")])
        style.configure("Browse.TButton", padding=6, relief="flat", background="#44475a", foreground="white", font=("Segoe UI", 10))
        style.map("Browse.TButton", background=[("active", "#6272a4")])
        style.configure("Convert.TButton", padding=8, relief="flat", background="#50fa7b", foreground="#1e1e2e", font=("Segoe UI", 11, "bold"))
        style.map("Convert.TButton", background=[("active", "#69ff94"), ("disabled", "#3d5a48")])
        style.configure("TProgressbar", thickness=12, troughcolor="#44475a", background="#6c63ff")

        header = tk.Label(self.root, text="Batch WebP → JPG Converter", bg="#1e1e2e", fg="#f8f8f2",
                          font=("Segoe UI", 16, "bold"))
        header.pack(pady=(24, 4))

        subtitle = tk.Label(self.root, text="Convert all .webp files in a folder to .jpg", bg="#1e1e2e", fg="#6272a4",
                            font=("Segoe UI", 10))
        subtitle.pack(pady=(0, 20))

        frame = tk.Frame(self.root, bg="#1e1e2e")
        frame.pack(fill="x", padx=40)

        # Source directory row
        tk.Label(frame, text="Source Directory", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        src_row = tk.Frame(frame, bg="#1e1e2e")
        src_row.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        frame.columnconfigure(0, weight=1)
        src_entry = tk.Entry(src_row, textvariable=self.source_dir, bg="#313244", fg="#f8f8f2",
                             insertbackground="white", relief="flat", font=("Segoe UI", 10), bd=6)
        src_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(src_row, text="Browse", style="Browse.TButton",
                   command=self._browse_source).pack(side="left", padx=(8, 0))

        # Output directory row
        tk.Label(frame, text="Output Directory", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 4))
        out_row = tk.Frame(frame, bg="#1e1e2e")
        out_row.grid(row=3, column=0, sticky="ew", pady=(0, 24))
        out_entry = tk.Entry(out_row, textvariable=self.output_dir, bg="#313244", fg="#f8f8f2",
                             insertbackground="white", relief="flat", font=("Segoe UI", 10), bd=6)
        out_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", style="Browse.TButton",
                   command=self._browse_output).pack(side="left", padx=(8, 0))

        # Options checkboxes
        style.configure("Option.TCheckbutton", background="#1e1e2e", foreground="#cdd6f4",
                        font=("Segoe UI", 10))
        style.map("Option.TCheckbutton", background=[("active", "#1e1e2e")])
        style.configure("Delete.TCheckbutton", background="#1e1e2e", foreground="#f38ba8",
                        font=("Segoe UI", 10))
        style.map("Delete.TCheckbutton", background=[("active", "#1e1e2e")])
        ttk.Checkbutton(self.root, text="Also process .jpg/.jpeg files (re-encode as baseline)",
                        variable=self.include_jpg, style="Option.TCheckbutton").pack(pady=(0, 4))
        ttk.Checkbutton(self.root, text="Delete source files after successful conversion",
                        variable=self.delete_source, style="Delete.TCheckbutton").pack(pady=(0, 12))

        # Convert button
        self.convert_btn = ttk.Button(self.root, text="Convert", style="Convert.TButton",
                                      command=self._start_conversion)
        self.convert_btn.pack(pady=(0, 16))

        # Progress bar
        self.progress = ttk.Progressbar(self.root, style="TProgressbar", length=520, mode="determinate")
        self.progress.pack(pady=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, bg="#1e1e2e", fg="#6272a4",
                                     font=("Segoe UI", 9))
        self.status_label.pack()

        # Log box
        log_frame = tk.Frame(self.root, bg="#1e1e2e")
        log_frame.pack(fill="both", expand=True, padx=40, pady=(10, 20))
        self.log_box = tk.Text(log_frame, bg="#181825", fg="#a6e3a1", relief="flat", font=("Consolas", 9),
                               height=6, state="disabled", wrap="word")
        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview, bg="#313244", troughcolor="#1e1e2e")
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _browse_source(self):
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_dir.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir.set(path)

    def _log(self, message, color=None):
        self.log_box.configure(state="normal")
        tag = None
        if color:
            tag = color
            self.log_box.tag_configure(tag, foreground=color)
        self.log_box.insert("end", message + "\n", tag or "")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _start_conversion(self):
        if self.is_running:
            return
        src = self.source_dir.get().strip()
        out = self.output_dir.get().strip()

        if not src:
            messagebox.showerror("Missing Input", "Please select a source directory.")
            return
        if not out:
            messagebox.showerror("Missing Input", "Please select an output directory.")
            return
        if not os.path.isdir(src):
            messagebox.showerror("Invalid Path", "Source directory does not exist.")
            return

        delete = self.delete_source.get()
        include_jpg = self.include_jpg.get()
        if delete and not messagebox.askyesno(
            "Confirm Delete",
            "Source files will be permanently deleted after successful conversion.\n\nProceed?"
        ):
            return

        self.is_running = True
        self.convert_btn.state(["disabled"])
        threading.Thread(target=self._run_conversion, args=(src, out, delete, include_jpg), daemon=True).start()

    def _run_conversion(self, src, out, delete_source=False, include_jpg=False):
        try:
            src_path = Path(src)
            webp_files = list(src_path.glob("*.webp"))
            jpg_files = (list(src_path.glob("*.jpg")) + list(src_path.glob("*.jpeg"))) if include_jpg else []

            all_files = webp_files + jpg_files
            if not all_files:
                msg = "No .webp or .jpg/.jpeg files found in source directory." if include_jpg else "No .webp files found in source directory."
                self.root.after(0, self._log, msg, "#ff5555")
                self.root.after(0, self.status_var.set, "No files found.")
                return

            os.makedirs(out, exist_ok=True)
            total = len(all_files)
            self.root.after(0, self.progress.configure, {"maximum": total, "value": 0})
            self.root.after(0, self._log, f"Found {len(webp_files)} .webp and {len(jpg_files)} .jpg/.jpeg file(s). Starting...")

            converted = 0
            failed = 0
            error_entries = []

            for i, src_file in enumerate(all_files, 1):
                is_jpg = src_file.suffix.lower() in (".jpg", ".jpeg")
                out_name = src_file.stem + ".jpg"
                out_path = Path(out) / out_name
                try:
                    with Image.open(src_file) as img:
                        # Capture quantization tables before converting to RGB
                        # (they are lost after convert, breaking quality="keep")
                        quantization = getattr(img, "quantization", None)
                        subsampling = img.info.get("subsampling", -1)
                        rgb = img.convert("RGB")
                        if is_jpg and quantization is not None:
                            # Baseline re-encode using original quantization tables (no recompression loss)
                            rgb.save(out_path, "JPEG", quantization=quantization,
                                     subsampling=subsampling, progressive=False)
                        else:
                            rgb.save(out_path, "JPEG", quality=95, progressive=False)
                    same_file = src_file.resolve() == out_path.resolve()
                    if delete_source and not same_file:
                        src_file.unlink()
                        self.root.after(0, self._log, f"  [{i}/{total}] {src_file.name} → {out_name} (source deleted)")
                    else:
                        self.root.after(0, self._log, f"  [{i}/{total}] {src_file.name} → {out_name}")
                    converted += 1
                except Exception as e:
                    tb = traceback.format_exc()
                    error_entries.append((src_file.name, str(e), tb))
                    self.root.after(0, self._log, f"  [{i}/{total}] FAILED: {src_file.name} — {e}", "#ff5555")
                    failed += 1
                self.root.after(0, self.progress.configure, {"value": i})
                self.root.after(0, self.status_var.set, f"Converting... {i}/{total}")

            log_path = None
            if error_entries:
                log_path = Path(out) / f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"BatchWebpConverter — Error Log\n")
                    f.write(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Source: {src}\n")
                    f.write(f"Output: {out}\n")
                    f.write("=" * 60 + "\n\n")
                    for name, msg, tb in error_entries:
                        f.write(f"File: {name}\n")
                        f.write(f"Error: {msg}\n")
                        f.write(f"Traceback:\n{tb}\n")
                        f.write("-" * 60 + "\n\n")
                self.root.after(0, self._log, f"Error log saved: {log_path.name}", "#f1fa8c")

            summary = f"Done. {converted} converted, {failed} failed."
            self.root.after(0, self._log, summary, "#50fa7b")
            self.root.after(0, self.status_var.set, summary)
        finally:
            self.is_running = False
            self.root.after(0, self.convert_btn.state, ["!disabled"])


if __name__ == "__main__":
    root = tk.Tk()
    app = WebpConverterApp(root)
    root.mainloop()
