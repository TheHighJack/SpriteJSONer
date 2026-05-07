import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from PIL import Image, ImageTk


# ─────────────────────────────────────────────────────────────────
# RULER CANVAS
# ─────────────────────────────────────────────────────────────────
class RulerCanvas(tk.Canvas):
    """Righello con guide draggabili."""
    TICK_COLOR = "#797876"
    GUIDE_COLOR = "#fdab43"
    RULER_BG = "#22211f"
    RULER_SIZE = 20

    def __init__(self, master, orientation, preview_ref=None, **kw):
        super().__init__(master, bg=self.RULER_BG, highlightthickness=0, **kw)
        self.orientation = orientation  # "h" or "v"
        self.preview_ref = preview_ref
        self._guides = []
        self._dragging_index = None
        self.px_per_unit = 32
        self.unit_label = "px"

        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self.redraw())

    def set_scale(self, px_per_unit, unit_label="px"):
        self.px_per_unit = max(1, int(px_per_unit))
        self.unit_label = unit_label
        self.redraw()

    def redraw(self, frame_size=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return

        self.create_rectangle(0, 0, w, h, fill=self.RULER_BG, outline="")

        step = max(1, int(self.px_per_unit))
        size = self.RULER_SIZE
        total = w if self.orientation == "h" else h

        pos = 0
        tick_n = 0
        while pos < total:
            major = (tick_n % 4 == 0)
            tick_len = size * 0.6 if major else size * 0.3

            if self.orientation == "h":
                self.create_line(pos, size - tick_len, pos, size, fill=self.TICK_COLOR, width=1)
                if major and pos > 0:
                    self.create_text(
                        pos + 2, 2,
                        text=str(tick_n * step),
                        fill=self.TICK_COLOR,
                        anchor="nw",
                        font=("Segoe UI", 7)
                    )
            else:
                self.create_line(size - tick_len, pos, size, pos, fill=self.TICK_COLOR, width=1)
                if major and pos > 0:
                    self.create_text(
                        2, pos + 2,
                        text=str(tick_n * step),
                        fill=self.TICK_COLOR,
                        anchor="nw",
                        font=("Segoe UI", 7)
                    )

            pos += step
            tick_n += 1

        if self.orientation == "h":
            self.create_line(0, size - 1, w, size - 1, fill="#393836")
        else:
            self.create_line(size - 1, 0, size - 1, h, fill="#393836")

        for g in self._guides:
            self._draw_guide(g)

    def _draw_guide(self, pos):
        size = self.RULER_SIZE
        if self.orientation == "h":
            self.create_line(pos, 0, pos, size, fill=self.GUIDE_COLOR, width=2, tags="guide")
        else:
            self.create_line(0, pos, size, pos, fill=self.GUIDE_COLOR, width=2, tags="guide")

    def _on_press(self, event):
        coord = event.x if self.orientation == "h" else event.y

        for i, g in enumerate(self._guides):
            if abs(coord - g) < 5:
                self._dragging_index = i
                return

        self._guides.append(coord)
        self._dragging_index = len(self._guides) - 1
        self._notify_preview()
        self.redraw()

    def _on_drag(self, event):
        if self._dragging_index is None:
            return

        coord = event.x if self.orientation == "h" else event.y
        coord = max(0, coord)
        self._guides[self._dragging_index] = coord
        self._notify_preview()
        self.redraw()

    def _on_release(self, event):
        self._dragging_index = None

    def remove_last(self):
        if self._guides:
            self._guides.pop()
            self._notify_preview()
            self.redraw()

    def remove_all(self):
        self._guides.clear()
        self._notify_preview()
        self.redraw()

    def get_guides(self):
        return list(self._guides)

    def set_guides(self, guides):
        self._guides = [max(0, int(g)) for g in guides]
        self._notify_preview()
        self.redraw()

    def _notify_preview(self):
        if self.preview_ref and hasattr(self.preview_ref, "redraw_guides"):
            self.preview_ref.redraw_guides()


# ─────────────────────────────────────────────────────────────────
# PREVIEW CANVAS
# ─────────────────────────────────────────────────────────────────
class PreviewCanvas(tk.Canvas):
    GUIDE_COLOR = "#fdab43"
    GUIDE_COLOR_V = "#4f98a3"
    HANDLE_FILL = "#4f98a3"
    HANDLE_ACTIVE = "#fdab43"
    HANDLE_SIZE = 12
    MIN_SIZE = 24

    def __init__(self, master, width=220, height=220, **kw):
        super().__init__(master, bg="#171614", highlightthickness=0, width=width, height=height, **kw)
        self.h_ruler = None
        self.v_ruler = None

        self.preview_w = int(width)
        self.preview_h = int(height)

        self._current_source_pil = None
        self._current_photo = None

        self._resize_mode = None
        self._drag_start = None
        self._start_size = None
        self._resize_callback = None

        self.bind("<Configure>", self._on_configure)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set_resize_callback(self, callback):
        self._resize_callback = callback

    def set_target_size(self, width, height, notify=False):
        width = max(self.MIN_SIZE, int(width))
        height = max(self.MIN_SIZE, int(height))

        changed = (width != self.preview_w or height != self.preview_h)
        self.preview_w = width
        self.preview_h = height

        self.config(width=width, height=height)

        if self.h_ruler is not None:
            self.h_ruler.config(width=width)
        if self.v_ruler is not None:
            self.v_ruler.config(height=height)

        self._render_frame()

        if changed and notify and self._resize_callback:
            self._resize_callback(width, height)

    def set_frame_pil(self, pil_img):
        self._current_source_pil = pil_img
        self._render_frame()

    def clear_frame(self):
        self._current_source_pil = None
        self._current_photo = None
        self.delete("all")


    def _render_frame(self):
        self.delete("all")

        if self._current_source_pil is not None:
            resized = self._current_source_pil.resize((self.preview_w, self.preview_h), Image.NEAREST)
            self._current_photo = ImageTk.PhotoImage(resized)
            self.create_image(0, 0, image=self._current_photo, anchor=tk.NW, tags="frame_img")

        self.redraw_guides()


    def redraw_guides(self):
        self.delete("guide_h", "guide_v")

        w = self.preview_w
        h = self.preview_h

        if self.h_ruler:
            for g in self.h_ruler.get_guides():
                self.create_line(g, 0, g, h, fill=self.GUIDE_COLOR, width=1, dash=(4, 3), tags="guide_h")

        if self.v_ruler:
            for g in self.v_ruler.get_guides():
                self.create_line(0, g, w, g, fill=self.GUIDE_COLOR_V, width=1, dash=(4, 3), tags="guide_v")



    def _hit_test_resize(self, x, y):
        hs = self.HANDLE_SIZE
        w = self.preview_w
        h = self.preview_h

        in_right = (w - hs <= x <= w) and (max(0, h // 2 - hs) <= y <= min(h, h // 2 + hs))
        in_bottom = (max(0, w // 2 - hs) <= x <= min(w, w // 2 + hs)) and (h - hs <= y <= h)
        in_corner = (w - hs <= x <= w) and (h - hs <= y <= h)

        if in_corner:
            return "corner"
        if in_right:
            return "right"
        if in_bottom:
            return "bottom"
        return None

    def _on_press(self, event):
        mode = self._hit_test_resize(event.x, event.y)
        if mode:
            self._resize_mode = mode
            self._drag_start = (event.x, event.y)
            self._start_size = (self.preview_w, self.preview_h)

    def _on_drag(self, event):
        if not self._resize_mode or not self._drag_start or not self._start_size:
            return

        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]

        start_w, start_h = self._start_size
        new_w, new_h = start_w, start_h

        if self._resize_mode in ("right", "corner"):
            new_w = start_w + dx
        if self._resize_mode in ("bottom", "corner"):
            new_h = start_h + dy

        self.set_target_size(new_w, new_h, notify=True)

    def _on_release(self, event):
        self._resize_mode = None
        self._drag_start = None
        self._start_size = None

    def _on_configure(self, event):
        # Mantieni il controllo logico della dimensione interna
        if event.width != self.preview_w or event.height != self.preview_h:
            self.preview_w = event.width
            self.preview_h = event.height
            if self.h_ruler is not None:
                self.h_ruler.config(width=self.preview_w)
            if self.v_ruler is not None:
                self.v_ruler.config(height=self.preview_h)
            self._render_frame()


# ─────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────
class SpritesheetEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Spritesheet JSON Editor")
        self.root.geometry("1420x930")
        self.root.configure(bg="#1c1b19")

        self.image_path = None
        self.pil_image = None
        self.output_path = None

        # Griglia / crop reale
        self.frame_w = tk.IntVar(value=256)
        self.frame_h = tk.IntVar(value=256)
        self.cols = tk.IntVar(value=5)
        self.rows = tk.IntVar(value=5)
        self.frame_count = tk.IntVar(value=25)
        self.fps = tk.IntVar(value=8)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        self.spacing_x = tk.IntVar(value=0)
        self.spacing_y = tk.IntVar(value=0)

        # Righello / preview
        self.guide_step = tk.IntVar(value=32)
        self.preview_frame = tk.IntVar(value=1)
        self.preview_size_w = tk.IntVar(value=220)
        self.preview_size_h = tk.IntVar(value=220)

        self._anim_frame = 0
        self._anim_job = None
        self._frames_cache = []
        self._loaded_json_path = None
        self._tk_sheet = None
        self._current_frame_idx = 0
        self._live_update_job = None
        self._internal_preview_update = False
        self._internal_preview_resize = False

        self._build_ui()
        self._bind_live_updates()

    # ─────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1c1b19")
        style.configure("TLabel", background="#1c1b19", foreground="#cdccca", font=("Segoe UI", 10))
        style.configure(
            "TButton",
            background="#01696f",
            foreground="#f9f8f5",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=6
        )
        style.map("TButton", background=[("active", "#0c4e54")])
        style.configure(
            "Import.TButton",
            background="#393836",
            foreground="#cdccca",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=6
        )
        style.map("Import.TButton", background=[("active", "#4f98a3")])
        style.configure(
            "Danger.TButton",
            background="#a12c7b",
            foreground="#f9f8f5",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=4
        )
        style.map("Danger.TButton", background=[("active", "#7d1e5e")])
        style.configure(
            "TSpinbox",
            fieldbackground="#2d2c2a",
            foreground="#cdccca",
            background="#2d2c2a",
            arrowcolor="#cdccca"
        )
        style.configure(
            "TLabelframe",
            background="#1c1b19",
            foreground="#4f98a3",
            font=("Segoe UI", 10, "bold")
        )
        style.configure("TLabelframe.Label", background="#1c1b19", foreground="#4f98a3")

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X, side=tk.TOP)

        ttk.Button(top, text="Apri Spritesheet", command=self.open_image).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top, text="Importa JSON", style="Import.TButton", command=self.import_json).pack(side=tk.LEFT, padx=(0, 8))
        self.lbl_file = ttk.Label(top, text="Nessun file selezionato", foreground="#797876")
        self.lbl_file.pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Salva JSON", command=self.save_json).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(top, text="Cartella output", command=self.choose_output).pack(side=tk.RIGHT, padx=(8, 0))
        self.lbl_output = ttk.Label(top, text="Output: stesso del file", foreground="#797876")
        self.lbl_output.pack(side=tk.RIGHT, padx=4)

        self.lbl_json_status = ttk.Label(
            self.root,
            text=" JSON: nessun JSON importato",
            foreground="#797876",
            background="#1c1b19",
            font=("Segoe UI", 9)
        )
        self.lbl_json_status.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 2))
        tk.Frame(self.root, height=1, bg="#262523").pack(fill=tk.X)

        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, padding=12, width=310)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        gf = ttk.LabelFrame(left, text="Griglia", padding=10)
        gf.pack(fill=tk.X, pady=(0, 8))
        self._spin_row(gf, "Larghezza frame (w):", self.frame_w, 1, 4096)
        self._spin_row(gf, "Altezza frame (h):", self.frame_h, 1, 4096)
        self._spin_row(gf, "Colonne:", self.cols, 1, 512)
        self._spin_row(gf, "Righe:", self.rows, 1, 512)
        self._spin_row(gf, "N° frame totali:", self.frame_count, 1, 9999)

        of = ttk.LabelFrame(left, text="Offset & Spaziatura", padding=10)
        of.pack(fill=tk.X, pady=(0, 8))
        self._spin_row(of, "Offset X:", self.offset_x, 0, 8192)
        self._spin_row(of, "Offset Y:", self.offset_y, 0, 8192)
        self._spin_row(of, "Spacing X:", self.spacing_x, 0, 2048)
        self._spin_row(of, "Spacing Y:", self.spacing_y, 0, 2048)

        af = ttk.LabelFrame(left, text="Anteprima Animazione", padding=10)
        af.pack(fill=tk.X, pady=(0, 8))
        self._spin_row(af, "FPS:", self.fps, 1, 60)
        self._spin_row(af, "Vai al frame:", self.preview_frame, 1, 9999)

        btn_row = ttk.Frame(af)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Play", command=self.start_anim).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_row, text="Stop", command=self.stop_anim).pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.lbl_frame_info = ttk.Label(left, text="Frame: --", foreground="#797876")
        self.lbl_frame_info.pack(pady=3)
        ttk.Button(left, text="Ricalcola griglia", command=self.refresh).pack(fill=tk.X, pady=(2, 0))

        pf = ttk.LabelFrame(left, text="Preview Size / frame_size", padding=10)
        pf.pack(fill=tk.X, pady=(10, 8))
        self._spin_row(pf, "Preview width:", self.preview_size_w, 24, 4096)
        self._spin_row(pf, "Preview height:", self.preview_size_h, 24, 4096)

        ttk.Label(
            pf,
            text="Puoi cambiare questi valori anche trascinando gli handle blu/arancio nella preview.",
            foreground="#797876",
            font=("Segoe UI", 8),
            wraplength=260,
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

        gd = ttk.LabelFrame(left, text="Guide & Righello", padding=10)
        gd.pack(fill=tk.X, pady=(0, 8))
        self._spin_row(gd, "Passo righello (px):", self.guide_step, 4, 512)
        ttk.Button(gd, text="Aggiorna righello", command=self._apply_guide_step).pack(fill=tk.X, pady=(4, 2))

        g_btn = ttk.Frame(gd)
        g_btn.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(
            g_btn, text="Rimuovi ultima H", style="Danger.TButton",
            command=lambda: self._remove_guide("h", "last")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(
            g_btn, text="Rimuovi ultima V", style="Danger.TButton",
            command=lambda: self._remove_guide("v", "last")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)

        g_btn2 = ttk.Frame(gd)
        g_btn2.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(
            g_btn2, text="Rimuovi tutte H", style="Danger.TButton",
            command=lambda: self._remove_guide("h", "all")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(
            g_btn2, text="Rimuovi tutte V", style="Danger.TButton",
            command=lambda: self._remove_guide("v", "all")
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)

        g_btn3 = ttk.Frame(gd)
        g_btn3.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(g_btn3, text="💾 Salva guide", command=self.save_guides).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(g_btn3, text="📂 Carica guide", command=self.load_guides).pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.lbl_guides_info = ttk.Label(
            left,
            text="Guide H: — | V: —",
            foreground="#797876",
            font=("Segoe UI", 8)
        )
        self.lbl_guides_info.pack(pady=(4, 0))

        json_lf = ttk.LabelFrame(left, text="JSON caricato — frame list", padding=8)
        json_lf.pack(fill=tk.X, pady=(8, 0))
        self.txt_json_info = tk.Text(
            json_lf,
            height=7,
            width=30,
            bg="#2d2c2a",
            fg="#cdccca",
            font=("Courier New", 8),
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.txt_json_info.pack(fill=tk.X)

        right = ttk.Frame(main, padding=8)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sheet_lf = ttk.LabelFrame(right, text="Spritesheet + Griglia", padding=4)
        sheet_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.canvas_scroll_x = tk.Scrollbar(sheet_lf, orient=tk.HORIZONTAL)
        self.canvas_scroll_y = tk.Scrollbar(sheet_lf, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(
            sheet_lf,
            bg="#2d2c2a",
            highlightthickness=0,
            xscrollcommand=self.canvas_scroll_x.set,
            yscrollcommand=self.canvas_scroll_y.set
        )
        self.canvas_scroll_x.config(command=self.canvas.xview)
        self.canvas_scroll_y.config(command=self.canvas.yview)
        self.canvas_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        preview_outer = ttk.LabelFrame(right, text="Anteprima Frame + Guide", padding=4)
        preview_outer.pack(anchor="w", pady=(0, 4))

        corner = tk.Canvas(
            preview_outer,
            width=RulerCanvas.RULER_SIZE,
            height=RulerCanvas.RULER_SIZE,
            bg="#22211f",
            highlightthickness=0
        )
        corner.grid(row=0, column=0)

        self.h_ruler = RulerCanvas(
            preview_outer,
            orientation="h",
            preview_ref=None,
            height=RulerCanvas.RULER_SIZE,
            width=self.preview_size_w.get()
        )
        self.h_ruler.grid(row=0, column=1, sticky="ew")

        self.v_ruler = RulerCanvas(
            preview_outer,
            orientation="v",
            preview_ref=None,
            width=RulerCanvas.RULER_SIZE,
            height=self.preview_size_h.get()
        )
        self.v_ruler.grid(row=1, column=0, sticky="ns")

        self.preview_canvas = PreviewCanvas(
            preview_outer,
            width=self.preview_size_w.get(),
            height=self.preview_size_h.get()
        )
        self.preview_canvas.grid(row=1, column=1, sticky="nw")
        self.preview_canvas.h_ruler = self.h_ruler
        self.preview_canvas.v_ruler = self.v_ruler
        self.preview_canvas.set_resize_callback(self._on_preview_canvas_resized)

        self.h_ruler.preview_ref = self.preview_canvas
        self.v_ruler.preview_ref = self.preview_canvas

        self.h_ruler.bind("<ButtonRelease-1>", lambda e: self._update_guide_label(), add="+")
        self.v_ruler.bind("<ButtonRelease-1>", lambda e: self._update_guide_label(), add="+")

        self._apply_guide_step()
        self._update_guide_label()
        self._sync_preview_geometry()

    def _bind_live_updates(self):
        live_vars = [
            self.frame_w, self.frame_h, self.cols, self.rows, self.frame_count,
            self.offset_x, self.offset_y, self.spacing_x, self.spacing_y
        ]
        for var in live_vars:
            var.trace_add("write", self._on_grid_param_change)

        self.guide_step.trace_add("write", self._on_guide_step_change)
        self.preview_frame.trace_add("write", self._on_preview_frame_change)
        self.preview_size_w.trace_add("write", self._on_preview_size_change)
        self.preview_size_h.trace_add("write", self._on_preview_size_change)

    def _spin_row(self, parent, label, var, from_, to_):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)

        ttk.Label(row, text=label, width=22, anchor="w").pack(side=tk.LEFT)
        sp = ttk.Spinbox(row, from_=from_, to=to_, textvariable=var, width=8)
        sp.pack(side=tk.LEFT)

        sp.bind("<Return>", lambda e: self._on_spin_commit())
        sp.bind("<FocusOut>", lambda e: self._on_spin_commit())
        sp.bind("<<Increment>>", lambda e: self._on_spin_commit())
        sp.bind("<<Decrement>>", lambda e: self._on_spin_commit())

        if label.startswith("Vai al frame"):
            self.preview_frame_spin = sp

    def _on_spin_commit(self):
        self.refresh()

    def _safe_int(self, var, default=0):
        try:
            return int(var.get())
        except Exception:
            return default

    def _on_grid_param_change(self, *_):
        self._schedule_refresh()

    def _on_guide_step_change(self, *_):
        self._apply_guide_step()

    def _on_preview_frame_change(self, *_):
        if self._internal_preview_update:
            return
        self._show_selected_frame()

    def _on_preview_size_change(self, *_):
        if self._internal_preview_resize:
            return
        self._sync_preview_geometry()
        self._cache_frames()
        self._render_current_selection()

    def _schedule_refresh(self):
        if self._live_update_job is not None:
            try:
                self.root.after_cancel(self._live_update_job)
            except Exception:
                pass
        self._live_update_job = self.root.after(25, self._refresh_now)

    def _refresh_now(self):
        self._live_update_job = None
        self.refresh()

    def _clamp_preview_frame(self):
        n = len(self._frames_cache) if self._frames_cache else self._safe_int(self.frame_count, 1)
        n = max(1, n)
        current = self._safe_int(self.preview_frame, 1)
        current = max(1, min(current, n))
        self._set_preview_frame(current, redraw=False)
        self._sync_preview_spin_range(n)
        return current, n

    def _sync_preview_spin_range(self, max_frame):
        try:
            if hasattr(self, "preview_frame_spin"):
                self.preview_frame_spin.config(from_=1, to=max(1, int(max_frame)))
        except Exception:
            pass

    def _set_preview_frame(self, frame_number, redraw=True):
        frame_number = max(1, int(frame_number))
        self._internal_preview_update = True
        try:
            self.preview_frame.set(frame_number)
        finally:
            self._internal_preview_update = False

        self._current_frame_idx = frame_number - 1
        if redraw:
            self._render_current_selection()

    def _show_selected_frame(self):
        if self._frames_cache:
            n = len(self._frames_cache)
            frame_number = self._safe_int(self.preview_frame, 1)
            frame_number = max(1, min(frame_number, n))

            if frame_number != self.preview_frame.get():
                self._set_preview_frame(frame_number, redraw=False)

            self._current_frame_idx = frame_number - 1
            self.preview_canvas.set_frame_pil(self._frames_cache[self._current_frame_idx])
            self.lbl_frame_info.config(text=f"Frame: {frame_number} / {n}")
            self._update_canvas()
        else:
            self._current_frame_idx = 0
            self.preview_canvas.clear_frame()
            total = max(1, self._safe_int(self.frame_count, 1))
            self.lbl_frame_info.config(text=f"Frame: 0 / {total}")
            self._update_canvas()

    def _render_current_selection(self):
        self._show_selected_frame()

    # ─────────────────────────────────────────────────────────────
    # PREVIEW SIZE
    # ─────────────────────────────────────────────────────────────
    def _sync_preview_geometry(self):
        pw = max(24, self._safe_int(self.preview_size_w, 220))
        ph = max(24, self._safe_int(self.preview_size_h, 220))
        self.preview_canvas.set_target_size(pw, ph, notify=False)

        try:
            self.h_ruler.config(width=pw)
            self.v_ruler.config(height=ph)
            self.h_ruler.redraw()
            self.v_ruler.redraw()
        except Exception:
            pass

    def _on_preview_canvas_resized(self, width, height):
        self._internal_preview_resize = True
        try:
            self.preview_size_w.set(int(width))
            self.preview_size_h.set(int(height))
        finally:
            self._internal_preview_resize = False

        self._sync_preview_geometry()
        self._cache_frames()
        self._render_current_selection()

    # ─────────────────────────────────────────────────────────────
    # GUIDE TOOLS
    # ─────────────────────────────────────────────────────────────
    def _apply_guide_step(self, *_):
        step = max(4, self._safe_int(self.guide_step, 32))
        self.h_ruler.set_scale(step, f"{step}px")
        self.v_ruler.set_scale(step, f"{step}px")

    def _remove_guide(self, axis, mode):
        ruler = self.h_ruler if axis == "h" else self.v_ruler
        if mode == "last":
            ruler.remove_last()
        else:
            ruler.remove_all()
        self._update_guide_label()

    def _update_guide_label(self):
        h = self.h_ruler.get_guides()
        v = self.v_ruler.get_guides()
        hs = ", ".join(str(int(g)) for g in h) if h else "—"
        vs = ", ".join(str(int(g)) for g in v) if v else "—"
        self.lbl_guides_info.config(text=f"Guide H: {hs} | V: {vs}")

    def save_guides(self):
        path = filedialog.asksaveasfilename(
            title="Salva guide",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return

        data = {
            "step": self._safe_int(self.guide_step, 32),
            "h_guides": self.h_ruler.get_guides(),
            "v_guides": self.v_ruler.get_guides(),
            "preview_size": {
                "w": self._safe_int(self.preview_size_w, 220),
                "h": self._safe_int(self.preview_size_h, 220)
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo("Salvato", f"Guide salvate in:\n{path}")

    def load_guides(self):
        path = filedialog.askopenfilename(
            title="Carica guide",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            self.guide_step.set(data.get("step", 32))
            self._apply_guide_step()

            preview_size = data.get("preview_size", {})
            if preview_size:
                self.preview_size_w.set(preview_size.get("w", self.preview_size_w.get()))
                self.preview_size_h.set(preview_size.get("h", self.preview_size_h.get()))

            self.h_ruler.set_guides(data.get("h_guides", []))
            self.v_ruler.set_guides(data.get("v_guides", []))
            self._update_guide_label()
            self._sync_preview_geometry()
            self._cache_frames()
            self._render_current_selection()

            messagebox.showinfo("Caricate", "Guide ripristinate correttamente.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare le guide:\n{e}")

    # ─────────────────────────────────────────────────────────────
    # FILE I/O
    # ─────────────────────────────────────────────────────────────
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Seleziona Spritesheet",
            filetypes=[("Immagini", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Tutti", "*.*")]
        )
        if not path:
            return
        self._load_image(path)

    def _load_image(self, path):
        if not path or not isinstance(path, str):
            return False

        path = os.path.normpath(path)
        if not os.path.isfile(path):
            return False

        try:
            test = Image.open(path)
            test.verify()
        except Exception:
            return False

        try:
            self.pil_image = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Errore immagine", f"Impossibile aprire l'immagine:\n{e}")
            return False

        self.image_path = path
        self.lbl_file.config(text=os.path.basename(path), foreground="#cdccca")

        if not self._loaded_json_path:
            w, h = self.pil_image.size
            fw, fh = self._safe_int(self.frame_w, 256), self._safe_int(self.frame_h, 256)
            c = max(1, w // max(1, fw))
            r = max(1, h // max(1, fh))
            self.cols.set(c)
            self.rows.set(r)
            self.frame_count.set(max(1, c * r))

        self.refresh()
        return True

    def choose_output(self):
        path = filedialog.askdirectory(title="Seleziona cartella output")
        if path:
            self.output_path = path
            self.lbl_output.config(text=f"Output: {os.path.basename(path)}", foreground="#cdccca")

    # ─────────────────────────────────────────────────────────────
    # JSON IMPORT
    # ─────────────────────────────────────────────────────────────
    def import_json(self):
        path = filedialog.askopenfilename(
            title="Importa JSON spritesheet",
            filetypes=[("JSON", "*.json"), ("Tutti", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere il JSON:\n{e}")
            return

        frames = data.get("frames", {})
        meta = data.get("meta", {})

        if not frames:
            messagebox.showwarning("Attenzione", "Il JSON non contiene frame validi.")
            return

        first_key = sorted(frames.keys(), key=lambda k: int(k) if str(k).isdigit() else 0)[0]
        first = frames[first_key]

        fw = int(first.get("w", 256))
        fh = int(first.get("h", 256))

        xs = sorted(set(int(v["x"]) for v in frames.values()))
        ys = sorted(set(int(v["y"]) for v in frames.values()))
        cols = len(xs) if xs else 1
        rows = len(ys) if ys else 1
        total = len(frames)
        ox = xs[0] if xs else 0
        oy = ys[0] if ys else 0
        sx = max(0, (xs[1] - xs[0] - fw)) if len(xs) > 1 else 0
        sy = max(0, (ys[1] - ys[0] - fh)) if len(ys) > 1 else 0

        self.frame_w.set(fw)
        self.frame_h.set(fh)
        self.cols.set(cols)
        self.rows.set(rows)
        self.frame_count.set(total)
        self.offset_x.set(ox)
        self.offset_y.set(oy)
        self.spacing_x.set(sx)
        self.spacing_y.set(sy)

        frame_size_meta = meta.get("frame_size", {})
        self.preview_size_w.set(int(frame_size_meta.get("w", fw)))
        self.preview_size_h.set(int(frame_size_meta.get("h", fh)))

        self._loaded_json_path = path
        self.lbl_json_status.config(
            text=f" JSON: {os.path.basename(path)} — {total} frame | crop {fw}×{fh}px | preview {self.preview_size_w.get()}×{self.preview_size_h.get()}px",
            foreground="#4f98a3"
        )

        json_dir = os.path.dirname(os.path.abspath(path))
        base = os.path.splitext(os.path.basename(path))[0]
        meta_image = str(meta.get("image", "")).strip()

        raw_candidates = [
            os.path.join(json_dir, base + ".png"),
            os.path.join(json_dir, base + ".jpg"),
            os.path.join(json_dir, base + ".jpeg"),
        ]

        if meta_image:
            raw_candidates.append(os.path.join(json_dir, os.path.basename(meta_image)))

        candidates = [c for c in raw_candidates if os.path.isfile(c)]
        auto_loaded = any(self._load_image(c) for c in candidates)

        if not auto_loaded:
            ans = messagebox.askyesno(
                "Spritesheet non trovata",
                f"Non ho trovato automaticamente la spritesheet per:\n{os.path.basename(path)}\n\nVuoi selezionarla manualmente?"
            )
            if ans:
                img_path = filedialog.askopenfilename(
                    title="Seleziona Spritesheet",
                    filetypes=[("Immagini", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Tutti", "*.*")]
                )
                if img_path:
                    self._load_image(img_path)
                else:
                    self.refresh()
            else:
                self.refresh()

        self._update_json_info_box(frames)
        self._sync_preview_spin_range(max(1, total))
        self._sync_preview_geometry()
        self._cache_frames()
        self._render_current_selection()

    def _update_json_info_box(self, frames):
        lines = []
        for k, v in sorted(frames.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0):
            lines.append(f"[{k}] x:{v['x']} y:{v['y']} w:{v['w']} h:{v['h']}")
        self.txt_json_info.config(state=tk.NORMAL)
        self.txt_json_info.delete("1.0", tk.END)
        self.txt_json_info.insert(tk.END, "\n".join(lines))
        self.txt_json_info.config(state=tk.DISABLED)

    # ─────────────────────────────────────────────────────────────
    # JSON EXPORT
    # ─────────────────────────────────────────────────────────────
    def save_json(self):
        if not self.image_path:
            messagebox.showwarning("Attenzione", "Carica prima una spritesheet.")
            return

        data = self._build_json()
        base = os.path.splitext(os.path.basename(self.image_path))[0]
        out_dir = self.output_path if self.output_path else os.path.dirname(self.image_path)
        out_file = os.path.join(out_dir, base + ".json")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self._update_json_info_box(data["frames"])
        self._loaded_json_path = out_file
        self.lbl_json_status.config(
            text=f" JSON salvato: {os.path.basename(out_file)} — frame_size {data['meta']['frame_size']['w']}×{data['meta']['frame_size']['h']}",
            foreground="#6daa45"
        )

        messagebox.showinfo("Salvato", f"JSON salvato in:\n{out_file}")

    def _build_json(self):
        fw = self._safe_int(self.frame_w, 256)
        fh = self._safe_int(self.frame_h, 256)
        cols = max(1, self._safe_int(self.cols, 1))
        rows = max(1, self._safe_int(self.rows, 1))
        total = max(1, self._safe_int(self.frame_count, 1))
        ox = self._safe_int(self.offset_x, 0)
        oy = self._safe_int(self.offset_y, 0)
        sx = self._safe_int(self.spacing_x, 0)
        sy = self._safe_int(self.spacing_y, 0)

        preview_w = max(24, self._safe_int(self.preview_size_w, fw))
        preview_h = max(24, self._safe_int(self.preview_size_h, fh))

        frames = {}
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= total:
                    break
                frames[str(idx)] = {
                    "x": ox + c * (fw + sx),
                    "y": oy + r * (fh + sy),
                    "w": fw,
                    "h": fh,
                    "duration": 1
                }
                idx += 1

        img_w = self.pil_image.size[0] if self.pil_image else cols * fw
        img_h = self.pil_image.size[1] if self.pil_image else rows * fh
        base_name = os.path.splitext(os.path.basename(self.image_path))[0] if self.image_path else "spritesheet"

        return {
            "frames": frames,
            "meta": {
                "image": base_name + ".png",
                "size": {"w": img_w, "h": img_h},
                "frame_size": {"w": preview_w, "h": preview_h}
            }
        }

    # ─────────────────────────────────────────────────────────────
    # CANVAS / GRID
    # ─────────────────────────────────────────────────────────────
    def refresh(self, *_):
        self._update_canvas()
        self._cache_frames()
        self._clamp_preview_frame()
        self._render_current_selection()

    def _update_canvas(self):
        self.canvas.delete("all")

        if not self.pil_image:
            self.canvas.create_text(
                200, 100,
                text="Carica una spritesheet o importa un JSON",
                fill="#797876",
                font=("Segoe UI", 12)
            )
            return

        fw = max(1, self._safe_int(self.frame_w, 256))
        fh = max(1, self._safe_int(self.frame_h, 256))
        cols = max(1, self._safe_int(self.cols, 1))
        rows = max(1, self._safe_int(self.rows, 1))
        total = max(1, self._safe_int(self.frame_count, 1))
        ox = self._safe_int(self.offset_x, 0)
        oy = self._safe_int(self.offset_y, 0)
        sx = self._safe_int(self.spacing_x, 0)
        sy = self._safe_int(self.spacing_y, 0)
        iw, ih = self.pil_image.size

        scale = min(1.0, 900 / max(iw, ih, 1))
        disp_w, disp_h = int(iw * scale), int(ih * scale)

        thumb = self.pil_image.resize((disp_w, disp_h), Image.NEAREST)
        self._tk_sheet = ImageTk.PhotoImage(thumb)
        self.canvas.config(scrollregion=(0, 0, disp_w, disp_h))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._tk_sheet)

        active_idx = self._current_frame_idx
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= total:
                    break

                x0 = (ox + c * (fw + sx)) * scale
                y0 = (oy + r * (fh + sy)) * scale
                x1 = x0 + fw * scale
                y1 = y0 + fh * scale

                active = idx == active_idx
                color = "#fdab43" if active else "#4f98a3"
                width = 2 if active else 1

                self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=width)
                self.canvas.create_text(
                    x0 + 4, y0 + 4,
                    text=str(idx),
                    fill=color,
                    anchor=tk.NW,
                    font=("Segoe UI", max(7, int(9 * scale)))
                )
                idx += 1

    def _cache_frames(self):
        self._frames_cache = []
        if not self.pil_image:
            return

        fw = max(1, self._safe_int(self.frame_w, 256))
        fh = max(1, self._safe_int(self.frame_h, 256))
        cols = max(1, self._safe_int(self.cols, 1))
        rows = max(1, self._safe_int(self.rows, 1))
        total = max(1, self._safe_int(self.frame_count, 1))
        ox = self._safe_int(self.offset_x, 0)
        oy = self._safe_int(self.offset_y, 0)
        sx = self._safe_int(self.spacing_x, 0)
        sy = self._safe_int(self.spacing_y, 0)

        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= total:
                    break

                x = ox + c * (fw + sx)
                y = oy + r * (fh + sy)
                crop = self.pil_image.crop((x, y, x + fw, y + fh))
                self._frames_cache.append(crop)
                idx += 1

    # ─────────────────────────────────────────────────────────────
    # ANIMATION / PREVIEW
    # ─────────────────────────────────────────────────────────────
    def _preview_count(self):
        return len(self._frames_cache) if self._frames_cache else max(1, self._safe_int(self.frame_count, 1))

    def start_anim(self):
        if not self._frames_cache:
            self._cache_frames()

        if not self._frames_cache:
            messagebox.showwarning("Attenzione", "Carica prima una spritesheet.")
            return

        self.stop_anim()
        start_idx = max(0, self._safe_int(self.preview_frame, 1) - 1)
        self._anim_frame = start_idx % len(self._frames_cache)
        self._tick()

    def stop_anim(self):
        if self._anim_job:
            try:
                self.root.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def _tick(self):
        if not self._frames_cache:
            return

        n = len(self._frames_cache)
        f = self._anim_frame % n
        self._show_frame_index(f)
        self._anim_frame = (f + 1) % n
        delay = max(16, int(1000 / max(1, self._safe_int(self.fps, 8))))
        self._anim_job = self.root.after(delay, self._tick)

    def _show_frame_index(self, idx):
        if not self._frames_cache:
            self._current_frame_idx = 0
            self.preview_canvas.clear_frame()
            self._update_canvas()
            return

        idx = max(0, min(int(idx), len(self._frames_cache) - 1))
        self._current_frame_idx = idx

        self._internal_preview_update = True
        try:
            self.preview_frame.set(idx + 1)
        finally:
            self._internal_preview_update = False

        self.preview_canvas.set_frame_pil(self._frames_cache[idx])
        self.lbl_frame_info.config(text=f"Frame: {idx + 1} / {len(self._frames_cache)}")
        self._update_canvas()

    # ─────────────────────────────────────────────────────────────
    # MAIN
    # ─────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    SpritesheetEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
