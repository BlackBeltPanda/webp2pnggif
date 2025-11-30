import os
import time
import tkinter as tk
import tkinter.font
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageSequence
from tkinterdnd2 import DND_FILES, TkinterDnD

# --- CORE CONVERSION LOGIC ---

def convert_webp(path: Path, output_path: Path):
    img = Image.open(path)
    
    try:
        exif = img.getexif()
    except Exception:
        exif = None

    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    is_animated = len(frames) > 1

    if is_animated:
        processed = []
        for f in frames:
            if f.mode == "RGBA":
                base = Image.new("RGBA", f.size, (255, 255, 255, 0))
                base.paste(f, mask=f.split()[3])
            else:
                base = Image.new("RGB", f.size, (255, 255, 255))
                base.paste(f)
            processed.append(base.convert("RGB"))

        processed[0].save(
            output_path,
            format="gif",
            save_all=True,
            append_images=processed[1:],
            optimize=True,
            duration=img.info.get("duration", 10),
            loop=img.info.get("loop", 0),
            quality=100,
            exif=exif,
        )
    else:
        frame = frames[0]
        if frame.mode not in ("RGBA", "RGB"):
            frame = frame.convert("RGBA")

        frame.save(
            output_path,
            format="png",
            optimize=True,
            exif=exif,
        )

# --- UI CONFIGURATION ---

COLORS = {
    "bg": "#ffffff",
    "panel_bg": "#f3f4f6",
    "accent": "#4f46e5",         # Indigo
    "accent_hover": "#4338ca",
    "text": "#1f2937",
    "subtext": "#6b7280",
    "list_bg": "#ffffff",
    "success": "#10b981",        # Green
    "warning": "#f59e0b"
}

FONTS = {
    "header": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "button": ("Segoe UI", 10, "bold")
}

# --- HELPER CLASSES ---

class ToolTip:
    """A floating tooltip window for long filenames."""
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text, x, y):
        if self.tipwindow or not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x+10}+{y+10}")
        
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#333333", foreground="#ffffff",
                         relief=tk.SOLID, borderwidth=0,
                         font=("Segoe UI", 9), padx=8, pady=4)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ModernConverterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WebP Converter Pro")
        # UPDATED: Decreased height from 550 to 450
        self.root.geometry("700x450")
        self.root.configure(bg=COLORS["bg"])

        # Enable Drag and Drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_files)

        self._setup_styles()
        self._build_layout()
        
        # Tooltip tracking logic
        self.tooltip = ToolTip(self.file_list)
        self.file_list.bind('<Motion>', self.on_list_motion)
        self.file_list.bind('<Leave>', lambda e: self.tooltip.hidetip())
        
        # Key bindings
        self.file_list.bind('<Delete>', lambda e: self.remove_selected())
        self.file_list.bind('<BackSpace>', lambda e: self.remove_selected())
        
        # Overflow/Resize detection
        self.file_list.bind('<Configure>', self.check_overflow)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background=COLORS["bg"])
        
        # Flat Buttons
        style.configure("TButton", 
                        background=COLORS["panel_bg"], 
                        foreground=COLORS["text"],
                        borderwidth=0, 
                        focuscolor="none",
                        font=FONTS["body"],
                        padding=6)
        style.map("TButton", background=[("active", "#e5e7eb")])

        # Accent Button
        style.configure("Accent.TButton", 
                        background=COLORS["accent"], 
                        foreground="white",
                        font=FONTS["button"])
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"])])

        # Labels
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
        style.configure("Sub.TLabel", foreground=COLORS["subtext"], font=FONTS["small"])

    def _build_layout(self):
        # 1. TOP HEADER
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        ttk.Label(header_frame, text="WebP Batch Converter", font=FONTS["header"]).pack(side="left")

        # 2. MAIN CONTENT
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=30)

        # -- File List Area --
        list_container = tk.Frame(content_frame, bg=COLORS["list_bg"], 
                                  highlightthickness=1, highlightbackground="#e5e7eb")
        list_container.pack(fill="both", expand=True, pady=(0, 10))

        self.file_list = tk.Listbox(
            list_container,
            selectmode="extended",
            bd=0, highlightthickness=0,
            bg=COLORS["list_bg"], fg=COLORS["text"],
            font=FONTS["body"],
            activestyle="none"
        )
        self.file_list.pack(fill="both", expand=True, padx=10, pady=10)

        # -- Overflow Indicator --
        self.overflow_lbl = tk.Label(list_container, text="▼", bg=COLORS["list_bg"], fg=COLORS["subtext"], font=("Segoe UI", 8))

        # -- Controls Row --
        controls_frame = ttk.Frame(content_frame)
        controls_frame.pack(fill="x", pady=(0, 10))

        # Left: File Actions
        ttk.Button(controls_frame, text="+ Add Files", command=self.add_files).pack(side="left", padx=(0, 10))
        ttk.Button(controls_frame, text="Remove Selected", command=self.remove_selected).pack(side="left")
        
        # Right: Output Path
        self.path_var = tk.StringVar(value="")
        ttk.Button(controls_frame, text="Select Output Folder", command=self.browse_folder).pack(side="right")
        self.path_lbl = ttk.Label(controls_frame, textvariable=self.path_var, style="Sub.TLabel")
        self.path_lbl.pack(side="right", padx=10)

        # 3. FOOTER / PROGRESS
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill="x", side="bottom", padx=30, pady=(0, 30))

        # Canvas Progress Bar
        self.loading_canvas = tk.Canvas(footer_frame, height=35, bg=COLORS["panel_bg"], highlightthickness=0)
        self.loading_canvas.pack(fill="x", pady=(0, 15))
        
        self.prog_rect = self.loading_canvas.create_rectangle(0, 0, 0, 35, fill=COLORS["accent"], width=0)
        self.prog_text = self.loading_canvas.create_text(0, 0, text="", fill=COLORS["text"], font=("Segoe UI", 10, "bold"))

        # Big Convert Button
        self.convert_btn = ttk.Button(footer_frame, text="START CONVERSION", style="Accent.TButton", command=self.convert)
        self.convert_btn.pack(fill="x", ipady=5)

    # --- INPUT LOGIC ---

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self._insert_files(files)

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("WebP files", "*.webp")])
        self._insert_files(files)

    def _insert_files(self, files):
        if not files: return
        self.reset_status()
        
        current_items = set(self.file_list.get(0, tk.END))
        for f in files:
            path_obj = Path(f)
            if str(path_obj) not in current_items and path_obj.suffix.lower() == ".webp":
                self.file_list.insert(tk.END, str(path_obj))
        
        self.check_overflow()

    def remove_selected(self):
        self.reset_status()
        selected = self.file_list.curselection()
        for index in reversed(selected):
            self.file_list.delete(index)
        self.check_overflow()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(str(Path(folder)))

    def on_list_motion(self, event):
        index = self.file_list.nearest(event.y)
        bbox = self.file_list.bbox(index)
        if not bbox or index == -1:
            self.tooltip.hidetip()
            return
        
        text = self.file_list.get(index)
        font = tk.font.Font(font=self.file_list['font']) 
        text_width = font.measure(text)
        list_width = self.file_list.winfo_width() - 20 

        if text_width > list_width:
            x_root, y_root = self.file_list.winfo_rootx(), self.file_list.winfo_rooty()
            self.tooltip.showtip(text, x_root + event.x + 15, y_root + bbox[1])
        else:
            self.tooltip.hidetip()

    def check_overflow(self, event=None):
        self.root.update_idletasks()
        if self.file_list.size() == 0:
            self.overflow_lbl.place_forget()
            return

        top, bottom = self.file_list.yview()
        if (bottom - top) < 0.99:
            self.overflow_lbl.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)
            self.overflow_lbl.lift()
        else:
            self.overflow_lbl.place_forget()

    # --- PROGRESS BAR LOGIC ---

    def reset_status(self):
        self.update_progress(0)

    def update_progress(self, percent, is_done=False):
        width = self.loading_canvas.winfo_width()
        fill_width = width * (percent / 100)
        
        bar_color = COLORS["success"] if is_done else COLORS["accent"]
        self.loading_canvas.coords(self.prog_rect, 0, 0, fill_width, 35)
        self.loading_canvas.itemconfig(self.prog_rect, fill=bar_color)
        
        center_x, center_y = width / 2, 35 / 2
        msg = "DONE!" if is_done else f"{int(percent)}%"
        if percent == 0 and not is_done: msg = ""
        
        text_color = "white" if (percent > 0 or is_done) else COLORS["text"]
        
        self.loading_canvas.coords(self.prog_text, center_x, center_y)
        self.loading_canvas.itemconfig(self.prog_text, text=msg, fill=text_color)
        self.root.update_idletasks()

    # --- CONVERSION LOGIC ---

    def ask_conflict_resolution(self, conflict_files):
        result = {"choice": None}

        def set_choice(choice):
            result["choice"] = choice
            popup.destroy()

        popup = tk.Toplevel(self.root)
        popup.title("File Conflict")
        popup.configure(bg="white")
        
        mw, mh, mx, my = self.root.winfo_width(), self.root.winfo_height(), self.root.winfo_x(), self.root.winfo_y()
        # UPDATED: Reduced size to 400x160
        pw, ph = 400, 160
        px, py = mx + (mw - pw) // 2, my + (mh - ph) // 2
        popup.geometry(f"{pw}x{ph}+{px}+{py}")

        # UPDATED: Reduced padding (pady=20 -> pady=(20, 10))
        tk.Label(popup, text=f"{len(conflict_files)} file(s) already exist in output.\nWhat should we do?",
                 bg="white", font=FONTS["body"], justify="center").pack(pady=(20, 10))

        btn_frame = tk.Frame(popup, bg="white")
        # UPDATED: Reduced padding (pady=10 -> pady=5)
        btn_frame.pack(pady=5)
        
        def mk_btn(txt, val, col=COLORS["panel_bg"], txt_col=COLORS["text"]):
            b = tk.Button(btn_frame, text=txt, command=lambda: set_choice(val),
                          bg=col, fg=txt_col, font=FONTS["body"], relief="flat", padx=15, pady=5)
            b.pack(side="left", padx=5)

        mk_btn("Overwrite", "overwrite", COLORS["warning"], "white")
        mk_btn("Rename", "rename", COLORS["accent"], "white")
        mk_btn("Skip", "skip")

        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)
        return result["choice"]

    def convert(self):
        files_str = self.file_list.get(0, tk.END)
        if not files_str:
            messagebox.showerror("Error", "No files in the list.")
            return

        files = [Path(f) for f in files_str]
        output_dir_str = self.path_var.get()
        
        if not output_dir_str:
            messagebox.showerror("Error", "Please select an output folder.")
            return
            
        output_dir = Path(output_dir_str)
        
        conflict_files = []
        for f in files:
            img = Image.open(f)
            frames_count = 0
            for _ in ImageSequence.Iterator(img):
                frames_count += 1
                if frames_count > 1: break
            
            ext = ".gif" if frames_count > 1 else ".png"
            img.close()
            
            if (output_dir / (f.stem + ext)).exists():
                conflict_files.append(f)

        resolution = None
        if conflict_files:
            resolution = self.ask_conflict_resolution(conflict_files)
            if resolution is None: return

        self.update_progress(0)
        total = len(files)

        for i, f in enumerate(files, start=1):
            try:
                img = Image.open(f)
                frames_count = 0
                for _ in ImageSequence.Iterator(img):
                    frames_count += 1
                    if frames_count > 1: break
                ext = ".gif" if frames_count > 1 else ".png"
                img.close()

                output_path = output_dir / (f.stem + ext)

                if resolution == "skip" and output_path.exists():
                    self.update_progress((i / total) * 100)
                    continue
                
                if resolution == "rename" and output_path.exists():
                    counter = 1
                    new_path = output_dir / f"{f.stem}-{counter}{ext}"
                    while new_path.exists():
                        counter += 1
                        new_path = output_dir / f"{f.stem}-{counter}{ext}"
                    output_path = new_path

                convert_webp(f, output_path)

            except Exception as e:
                print(f"Error converting {f.name}: {e}")
            
            self.update_progress((i / total) * 100)

        self.update_progress(100, is_done=True)
        
        self.file_list.delete(0, tk.END)
        self.check_overflow()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ModernConverterUI(root)
    root.mainloop()