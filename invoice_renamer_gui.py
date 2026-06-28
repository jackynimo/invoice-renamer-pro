import os
import re
import gc
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

# ── Find base path ────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUNDLED_TESS = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
DEFAULT_TESS = BUNDLED_TESS if os.path.exists(BUNDLED_TESS) \
               else r"C:\Program Files\Tesseract-OCR\tesseract.exe"

try:
    import fitz
    import pytesseract
    from PIL import Image, ImageFilter, ImageEnhance
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)

# ═══════════════════════════════════════════════════════════════════════════
#  OCR ENGINE
# ═══════════════════════════════════════════════════════════════════════════
CODE_PATTERN = re.compile(r'\b(IN\d{8}|BSI\d{7})\b', re.IGNORECASE)
DOC_NO_LINE  = re.compile(r'Document\s+No[:\s]+([A-Z0-9]{8,12})', re.IGNORECASE)

def fix_code_string(code):
    code = code.upper().replace('O','0').replace('Q','0')
    code = re.sub(r'^1N', 'IN', code)
    code = re.sub(r'^lN', 'IN', code)
    code = re.sub(r'^B5', 'BS', code)
    if code.startswith('IN'):
        code = 'IN' + code[2:][:8]
    elif code.startswith('BSI'):
        code = 'BSI' + code[3:][:7]
    return code

def correct_ocr_text(text):
    fixes = [
        (r'\b1N\b','IN'),(r'\blN\b','IN'),(r'\b\|N\b','IN'),
        (r'\bBSl\b','BSI'),(r'\bB5I\b','BSI'),(r'\bB5l\b','BSI'),(r'\bB51\b','BSI'),
    ]
    for p,r in fixes:
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    def fix_digits(m):
        return m.group(0).upper().replace('O','0').replace('Q','0')
    text = re.sub(r'\bIN[0-9OoQq]{7,10}\b',  fix_digits, text, flags=re.IGNORECASE)
    text = re.sub(r'\bBSI[0-9OoQq]{6,9}\b',  fix_digits, text, flags=re.IGNORECASE)
    return text

def find_code_in_text(text):
    m = DOC_NO_LINE.search(text)
    if m:
        candidate = fix_code_string(m.group(1))
        if CODE_PATTERN.match(candidate):
            return candidate
    corrected = correct_ocr_text(text)
    m = CODE_PATTERN.search(corrected)
    if m:
        return m.group(0).upper()
    return None

def extract_code(pdf_path, tesseract_path, dpi=200):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    try:
        with fitz.open(pdf_path) as doc:
            page = doc[0]
            pix  = page.get_pixmap(dpi=dpi)
            img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pix  = None
        for mode in ['raw','gray','sharp']:
            if mode == 'raw':   proc = img
            elif mode == 'gray': proc = ImageEnhance.Contrast(img.convert("L")).enhance(2.0)
            else:               proc = img.filter(ImageFilter.SHARPEN)
            text = pytesseract.image_to_string(proc)
            code = find_code_in_text(text)
            if code: return code
        return None
    except Exception:
        return None
    finally:
        img = None
        gc.collect()

def unique_path(folder, name):
    candidate = os.path.join(folder, name)
    stem, ext = os.path.splitext(name)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem}_{counter}{ext}")
        counter += 1
    return candidate

# ═══════════════════════════════════════════════════════════════════════════
#  GUI  — compact layout, START button always visible
# ═══════════════════════════════════════════════════════════════════════════
BG      = "#0f1117"
CARD    = "#1a1d27"
ACCENT  = "#00d4aa"
ACCENT2 = "#0099ff"
TEXT    = "#e8eaf0"
SUBTEXT = "#7a7f9a"
SUCCESS = "#00c97a"
WARNING = "#ffb547"
DANGER  = "#ff5470"
BORDER  = "#2a2d3e"

class InvoiceRenamerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Invoice Renamer Pro")
        # Use full screen size minus taskbar
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{min(780,sw)}x{min(sh-60,700)}+0+0")
        self.resizable(True, True)
        self.configure(bg=BG)

        self.folder_var    = tk.StringVar(value="")
        self.tesseract_var = tk.StringVar(value=DEFAULT_TESS)
        self.threads_var   = tk.IntVar(value=2)
        self.dpi_var       = tk.IntVar(value=200)
        self.running       = False
        self._stop_flag    = threading.Event()
        self.renamed_count = 0
        self.skipped_count = 0
        self.error_count   = 0

        self._build_ui()
        self._check_tess()

    def _check_tess(self):
        if os.path.exists(self.tesseract_var.get()):
            self._log(f"✓ Tesseract found: {self.tesseract_var.get()}", "ok")
        else:
            self._log("⚠ Tesseract not found — check path below", "skip")

    def _build_ui(self):
        # ── TOP: fixed controls ───────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=(10,0))

        # Title
        title_row = tk.Frame(top, bg=BG)
        title_row.pack(fill="x")
        tk.Label(title_row, text="Invoice Renamer Pro",
                 font=("Arial",18,"bold"), bg=BG, fg=ACCENT).pack(side="left")

        # Folder
        tk.Label(top, text="Invoice Folder:", font=("Arial",9,"bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w", pady=(8,2))
        f1 = tk.Frame(top, bg=BG)
        f1.pack(fill="x")
        tk.Entry(f1, textvariable=self.folder_var, font=("Courier",9),
                 bg=CARD, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", highlightthickness=1,
                 highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(f1, text="Browse", command=self._pick_folder,
                  bg=ACCENT, fg=BG, font=("Arial",9,"bold"),
                  relief="flat", padx=10, cursor="hand2"
                  ).pack(side="left", padx=(6,0))

        # Tesseract
        tk.Label(top, text="Tesseract Path:", font=("Arial",9,"bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w", pady=(6,2))
        f2 = tk.Frame(top, bg=BG)
        f2.pack(fill="x")
        tk.Entry(f2, textvariable=self.tesseract_var, font=("Courier",9),
                 bg=CARD, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", highlightthickness=1,
                 highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(f2, text="Browse", command=self._pick_tesseract,
                  bg=BORDER, fg=TEXT, font=("Arial",9),
                  relief="flat", padx=10, cursor="hand2"
                  ).pack(side="left", padx=(6,0))

        # Settings
        tk.Label(top, text="Settings:", font=("Arial",9,"bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w", pady=(6,2))
        srow = tk.Frame(top, bg=BG)
        srow.pack(fill="x")
        tk.Label(srow, text="Threads:", font=("Arial",9), bg=BG, fg=SUBTEXT).pack(side="left")
        for v in [1,2,4]:
            tk.Radiobutton(srow, text=str(v), variable=self.threads_var, value=v,
                           font=("Arial",9), bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG).pack(side="left", padx=4)
        tk.Label(srow, text="  DPI:", font=("Arial",9), bg=BG, fg=SUBTEXT).pack(side="left")
        for v in [150,200,300]:
            tk.Radiobutton(srow, text=str(v), variable=self.dpi_var, value=v,
                           font=("Arial",9), bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG).pack(side="left", padx=4)

        # Stats
        stats = tk.Frame(top, bg=CARD)
        stats.pack(fill="x", pady=(8,0))
        self.stat_total   = self._stat(stats, "0", "TOTAL")
        tk.Frame(stats, bg=BORDER, width=1).pack(side="left", fill="y", pady=4)
        self.stat_renamed = self._stat(stats, "0", "RENAMED", SUCCESS)
        tk.Frame(stats, bg=BORDER, width=1).pack(side="left", fill="y", pady=4)
        self.stat_skipped = self._stat(stats, "0", "SKIPPED", WARNING)
        tk.Frame(stats, bg=BORDER, width=1).pack(side="left", fill="y", pady=4)
        self.stat_errors  = self._stat(stats, "0", "ERRORS",  DANGER)

        # Progress
        self.progress_canvas = tk.Canvas(top, height=6, bg=BORDER,
                                         highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(6,0))
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=ACCENT, outline="")
        self.status_var = tk.StringVar(value="Ready — select a folder and press START")
        tk.Label(top, textvariable=self.status_var,
                 font=("Courier",8), bg=BG, fg=SUBTEXT, anchor="w"
                 ).pack(fill="x")

        # ── BUTTONS — always visible ──────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=6)

        self.start_btn = tk.Button(btn_frame, text="▶  START RENAMING",
                                   command=self._start,
                                   font=("Arial",12,"bold"),
                                   bg=ACCENT, fg=BG,
                                   activebackground=ACCENT2,
                                   relief="flat", padx=24, pady=10,
                                   cursor="hand2")
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(btn_frame, text="■  STOP",
                                  command=self._stop,
                                  font=("Arial",12,"bold"),
                                  bg=BORDER, fg=TEXT,
                                  relief="flat", padx=16, pady=10,
                                  state="disabled", cursor="hand2")
        self.stop_btn.pack(side="left", padx=(10,0))

        tk.Button(btn_frame, text="Clear Log", command=self._clear_log,
                  font=("Arial",9), bg=BORDER, fg=TEXT,
                  relief="flat", padx=10, pady=10, cursor="hand2"
                  ).pack(side="right")

        # ── LOG — fills remaining space ───────────────────────────────────
        log_frame = tk.Frame(self, bg=CARD)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0,10))

        self.log_text = tk.Text(log_frame, bg=CARD, fg=TEXT,
                                font=("Courier",9), relief="flat",
                                state="disabled", wrap="none",
                                insertbackground=ACCENT)
        scroll = tk.Scrollbar(log_frame, command=self.log_text.yview, bg=CARD)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=6)
        self.log_text.tag_config("ok",   foreground=SUCCESS)
        self.log_text.tag_config("skip", foreground=WARNING)
        self.log_text.tag_config("err",  foreground=DANGER)
        self.log_text.tag_config("info", foreground=SUBTEXT)

    def _stat(self, parent, value, label, color=TEXT):
        f = tk.Frame(parent, bg=CARD)
        f.pack(side="left", expand=True, fill="x", padx=10, pady=6)
        v = tk.Label(f, text=value, font=("Arial",18,"bold"), bg=CARD, fg=color)
        v.pack()
        tk.Label(f, text=label, font=("Arial",7), bg=CARD, fg=SUBTEXT).pack()
        return v

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Select Invoice Folder")
        if path: self.folder_var.set(path)

    def _pick_tesseract(self):
        path = filedialog.askopenfilename(
            title="Find tesseract.exe",
            filetypes=[("Executable","*.exe"),("All files","*.*")])
        if path: self.tesseract_var.set(path)

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0","end")
        self.log_text.config(state="disabled")

    def _log(self, msg, tag="info"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg+"\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _update_stats(self, total, renamed, skipped, errors):
        self.stat_total.config(text=str(total))
        self.stat_renamed.config(text=str(renamed))
        self.stat_skipped.config(text=str(skipped))
        self.stat_errors.config(text=str(errors))

    def _update_progress(self, done, total):
        self.progress_canvas.update_idletasks()
        w = self.progress_canvas.winfo_width()
        if total > 0:
            self.progress_canvas.coords(self.progress_bar, 0, 0, int(w*done/total), 6)

    def _start(self):
        if not IMPORTS_OK:
            messagebox.showerror("Missing Libraries",
                f"Required library not found:\n{IMPORT_ERROR}\n\n"
                "Run:  pip install pymupdf pytesseract Pillow")
            return
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        tess = self.tesseract_var.get().strip()
        if not os.path.exists(tess):
            messagebox.showerror("Tesseract Not Found",
                f"Cannot find:\n{tess}\n\nClick Browse to locate tesseract.exe")
            return
        self._stop_flag.clear()
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.renamed_count = self.skipped_count = self.error_count = 0
        threading.Thread(target=self._run_worker,
                         args=(folder, tess, self.threads_var.get(), self.dpi_var.get()),
                         daemon=True).start()

    def _stop(self):
        self._stop_flag.set()
        self.status_var.set("Stopping after current file…")

    def _run_worker(self, folder, tess_path, workers, dpi):
        from concurrent.futures import ThreadPoolExecutor, as_completed

        log_file  = os.path.join(folder, "rename_log.txt")
        all_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]

        processed = set()
        if os.path.exists(log_file):
            with open(log_file,'r',encoding='utf-8') as f:
                for line in f:
                    for prefix in ("RENAMED: ","SKIPPED (no code found): ","SKIPPED (cannot read): "):
                        if line.strip().startswith(prefix):
                            processed.add(line.strip()[len(prefix):].split(" →")[0].strip())

        to_do = [f for f in all_files if f not in processed]
        total = len(to_do)

        self.after(0, lambda: self.status_var.set(f"Found {len(all_files)} PDFs — processing {total}…"))
        self.after(0, lambda: self._update_stats(total,0,0,0))

        if total == 0:
            self.after(0, lambda: self.status_var.set("Nothing to process — all files already done."))
            self.after(0, self._finish)
            return

        done = 0
        log_lock = threading.Lock()

        def process(filename):
            if self._stop_flag.is_set():
                return {"file": filename, "status": "stopped"}
            code = extract_code(os.path.join(folder, filename), tess_path, dpi)
            if not code:
                return {"file": filename, "status": "skipped"}
            new_name = re.sub(r'[\\/*?:"<>|]', "_", f"{code}.pdf")
            new_path = unique_path(folder, new_name)
            try:
                os.rename(os.path.join(folder, filename), new_path)
                return {"file": filename, "status": "renamed", "new_name": os.path.basename(new_path)}
            except Exception as e:
                return {"file": filename, "status": "error", "reason": str(e)}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process, f): f for f in to_do}
            for future in as_completed(futures):
                r = future.result()
                done += 1
                if r["status"] == "renamed":
                    self.renamed_count += 1
                    self.after(0, lambda m=f"✓ {r['file']}  →  {r['new_name']}": self._log(m,"ok"))
                    with log_lock:
                        with open(log_file,'a',encoding='utf-8') as lf:
                            lf.write(f"RENAMED: {r['file']} → {r['new_name']}\n")
                elif r["status"] == "skipped":
                    self.skipped_count += 1
                    self.after(0, lambda m=f"– {r['file']}  (no code found)": self._log(m,"skip"))
                    with log_lock:
                        with open(log_file,'a',encoding='utf-8') as lf:
                            lf.write(f"SKIPPED (no code found): {r['file']}\n")
                elif r["status"] == "error":
                    self.error_count += 1
                    self.after(0, lambda m=f"✗ {r['file']}  ERROR: {r.get('reason','')}": self._log(m,"err"))

                rc,sc,ec,d2 = self.renamed_count,self.skipped_count,self.error_count,done
                self.after(0, lambda d=d2,t=total,r=rc,s=sc,e=ec: (
                    self._update_stats(t,r,s,e),
                    self._update_progress(d,t),
                    self.status_var.set(f"Processing {d}/{t}  |  Renamed: {r}  Skipped: {s}")
                ))
                if self._stop_flag.is_set():
                    break

        self.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        r,s,e = self.renamed_count,self.skipped_count,self.error_count
        self.status_var.set(f"✅ Done!  Renamed: {r}  Skipped: {s}  Errors: {e}")
        self._log(f"\n── Finished ──  Renamed: {r}  Skipped: {s}  Errors: {e}","info")
        self._update_progress(1,1)

if __name__ == "__main__":
    app = InvoiceRenamerApp()
    app.mainloop()
