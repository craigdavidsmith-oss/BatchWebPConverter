import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
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
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.delete_source = tk.BooleanVar(value=False)
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

        # Delete source checkbox
        style.configure("Delete.TCheckbutton", background="#1e1e2e", foreground="#f38ba8",
                        font=("Segoe UI", 10))
        style.map("Delete.TCheckbutton", background=[("active", "#1e1e2e")])
        ttk.Checkbutton(self.root, text="Delete source .webp files after successful conversion",
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
        if delete and not messagebox.askyesno(
            "Confirm Delete",
            "Source .webp files will be permanently deleted after conversion.\n\nProceed?"
        ):
            return

        self.is_running = True
        self.convert_btn.state(["disabled"])
        threading.Thread(target=self._run_conversion, args=(src, out, delete), daemon=True).start()

    def _run_conversion(self, src, out, delete_source=False):
        try:
            webp_files = list(Path(src).glob("*.webp"))
            if not webp_files:
                self.root.after(0, self._log, "No .webp files found in source directory.", "#ff5555")
                self.root.after(0, self.status_var.set, "No .webp files found.")
                return

            os.makedirs(out, exist_ok=True)
            total = len(webp_files)
            self.root.after(0, self.progress.configure, {"maximum": total, "value": 0})
            self.root.after(0, self._log, f"Found {total} file(s). Starting conversion...")

            converted = 0
            failed = 0
            for i, webp_path in enumerate(webp_files, 1):
                jpg_name = webp_path.stem + ".jpg"
                jpg_path = Path(out) / jpg_name
                try:
                    with Image.open(webp_path) as img:
                        rgb = img.convert("RGB")
                        rgb.save(jpg_path, "JPEG", quality=95)
                    if delete_source:
                        webp_path.unlink()
                        self.root.after(0, self._log, f"  [{i}/{total}] {webp_path.name} → {jpg_name} (source deleted)")
                    else:
                        self.root.after(0, self._log, f"  [{i}/{total}] {webp_path.name} → {jpg_name}")
                    converted += 1
                except Exception as e:
                    self.root.after(0, self._log, f"  [{i}/{total}] FAILED: {webp_path.name} — {e}", "#ff5555")
                    failed += 1
                self.root.after(0, self.progress.configure, {"value": i})
                self.root.after(0, self.status_var.set, f"Converting... {i}/{total}")

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
