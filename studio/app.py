"""
FoxVC Desktop Studio (Fox Den Master Edition)
A distinct, highly focused development environment for authoring, diagnosing,
disassembling, and compiling FoxVC programs with real-time 3D/2D visual stage
and zero-dependency standalone binary compilation.
"""

import os
import sys
import time
import math
import re
from typing import Any, Optional, Dict, List, Tuple

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    HAS_TKINTER = True
    CanvasBase = tk.Canvas
except (ImportError, ModuleNotFoundError):
    HAS_TKINTER = False
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    CanvasBase = object

import engine.runtime as rt
from engine.runner import run_foxvc, run_foxvc_diagnostic
from engine.lexer import Lexer
from engine.parser import Parser
from engine.bytecode import BytecodeCompiler
from engine.builder import StandaloneCompiler, BuildError
from engine.formatter import FoxFormatter
from engine.tester import FoxTestRunner


class LineNumbers(CanvasBase):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.configure(width=48, bg="#0A090C", highlightthickness=0, bd=0)

    def redraw(self):
        self.delete("all")
        if not self.text_widget:
            return
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0].zfill(2)
            self.create_text(36, y + 4, anchor="ne", text=linenum, fill="#524855", font=("Monospace", 9, "bold"))
            i = self.text_widget.index(f"{i}+1line")


class DocumentTab:
    def __init__(self, filepath=None, title="untitled.fox", content=""):
        self.filepath = filepath
        self.title = title
        self.is_modified = False
        self.content = content


class Stage3DWindow(tk.Toplevel):
    """
    Standalone 60 FPS 3D / 2D Rotating Geometry Stage Window.
    Renders real-time trigonometric vector transformations and polygon projections.
    """
    def __init__(self, parent, scene=None, title_suffix="3D Rotating Geometry"):
        super().__init__(parent)
        self.scene = scene
        self.title(f"🦊 FoxVC Visual Stage — {title_suffix}")
        self.geometry("820x620")
        self.minsize(520, 420)
        self.configure(bg="#07060A")

        self.is_paused = False
        self.start_time = time.time()
        self.angle_x = 0.4
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.speed = 1.0
        self.show_wireframe = True

        # 3D Cube Vertices (x, y, z)
        self.cube_vertices = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
            [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1]
        ]
        # Edges connecting vertex pairs
        self.cube_edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        # Top Control Bar
        bar = tk.Frame(self, bg="#0E0C14", height=38)
        bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(bar, text="🌌 3D ROTATING STAGE", bg="#0E0C14", fg="#FF7A00", font=("DejaVu Sans", 9, "bold")).pack(side=tk.LEFT, padx=12, pady=6)
        self.fps_lbl = tk.Label(bar, text="60 FPS | Trigonometric Projection", bg="#0E0C14", fg="#38BDF8", font=("DejaVu Sans", 8))
        self.fps_lbl.pack(side=tk.LEFT, padx=6)

        self.btn_pause = tk.Button(bar, text="⏸ Pause", command=self.toggle_pause, bg="#1B1726", fg="#EDE8E1", bd=0, padx=10, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2")
        self.btn_pause.pack(side=tk.RIGHT, padx=6)

        tk.Button(bar, text="⚡ Speed +", command=self.speed_up, bg="#1B1726", fg="#38BDF8", bd=0, padx=8, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2").pack(side=tk.RIGHT, padx=3)
        tk.Button(bar, text="🐌 Speed -", command=self.speed_down, bg="#1B1726", fg="#A89E93", bd=0, padx=8, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2").pack(side=tk.RIGHT, padx=3)
        tk.Button(bar, text="💾 Export SVG", command=self.export_svg, bg="#1B1726", fg="#10B981", bd=0, padx=10, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2").pack(side=tk.RIGHT, padx=6)

        # Drawing Canvas
        self.canvas = tk.Canvas(self, bg="#07060A", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._start_render_loop()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.config(text="▶ Play" if self.is_paused else "⏸ Pause")

    def speed_up(self):
        self.speed = min(4.0, self.speed + 0.3)

    def speed_down(self):
        self.speed = max(0.2, self.speed - 0.3)

    def export_svg(self):
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("Vector SVG", "*.svg"), ("All Files", "*.*")])
        if not path:
            return
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}" style="background:#07060A">']
        svg.append(f'<text x="20" y="30" fill="#FF7A00" font-family="sans-serif" font-size="14" font-weight="bold">FoxVC 3D Spatial Vector Snapshot</text>')
        # Export wireframe lines
        cx, cy = cw / 2, ch / 2
        scale = min(cw, ch) * 0.28
        proj_pts = []
        for x, y, z in self.cube_vertices:
            # Y rotation
            x1 = x * math.cos(self.angle_y) - z * math.sin(self.angle_y)
            z1 = x * math.sin(self.angle_y) + z * math.cos(self.angle_y)
            # X rotation
            y1 = y * math.cos(self.angle_x) - z1 * math.sin(self.angle_x)
            z2 = y * math.sin(self.angle_x) + z1 * math.cos(self.angle_x) + 3.0
            fov = scale / z2
            proj_pts.append((cx + x1 * fov, cy + y1 * fov))

        for u, v in self.cube_edges:
            x1, y1 = proj_pts[u]
            x2, y2 = proj_pts[v]
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#FF7A00" stroke-width="2"/>')
        svg.append('</svg>')

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))
        messagebox.showinfo("Export Success", f"Vector SVG snapshot exported successfully:\n{path}")

    def _start_render_loop(self):
        def loop():
            if not self.winfo_exists():
                return
            if not self.is_paused:
                # If scene has native renderer, delegate to it
                if self.scene and hasattr(self.scene, "render_frame_to_canvas"):
                    t = time.time() - self.start_time
                    cw = self.canvas.winfo_width() or 800
                    ch = self.canvas.winfo_height() or 600
                    self.scene.render_frame_to_canvas(self.canvas, cw, ch, t)
                else:
                    self._render_3d_frame()

            self.after(16, loop)

        self.after(50, loop)

    def _render_3d_frame(self):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        cx, cy = cw / 2, ch / 2

        self.angle_y += 0.025 * self.speed
        self.angle_x += 0.012 * self.speed
        self.angle_z += 0.008 * self.speed

        scale = min(cw, ch) * 0.28
        proj_pts = []

        # Coordinate Grid & Horizon
        self.canvas.create_line(0, cy + 180, cw, cy + 180, fill="#181524", width=1)
        self.canvas.create_text(cx, ch - 22, text="[FoxVC Vector Core] 60 FPS Trigonometric Transform", fill="#5A4F6A", font=("DejaVu Sans", 8))

        # Rotate and project vertices
        for x, y, z in self.cube_vertices:
            # Rotate Y
            x1 = x * math.cos(self.angle_y) - z * math.sin(self.angle_y)
            z1 = x * math.sin(self.angle_y) + z * math.cos(self.angle_y)
            # Rotate X
            y1 = y * math.cos(self.angle_x) - z1 * math.sin(self.angle_x)
            z2 = y * math.sin(self.angle_x) + z1 * math.cos(self.angle_x)
            # Perspective projection
            depth = z2 + 3.2
            fov = scale / depth
            px = cx + x1 * fov
            py = cy + y1 * fov
            proj_pts.append((px, py, depth))

        # Render Edges
        for u, v in self.cube_edges:
            x1, y1, d1 = proj_pts[u]
            x2, y2, d2 = proj_pts[v]
            # Depth cueing color
            avg_d = (d1 + d2) / 2
            edge_color = "#FF7A00" if avg_d < 3.2 else "#9A4A00"
            self.canvas.create_line(x1, y1, x2, y2, fill=edge_color, width=2)

        # Render Vertices
        for idx, (px, py, depth) in enumerate(proj_pts):
            r = 4 if depth < 3.2 else 3
            v_color = "#38BDF8" if depth < 3.2 else "#1E40AF"
            self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=v_color, outline="#FFFFFF" if depth < 3.0 else "")


class FoxVCStudio:
    """Fox Den Studio: Custom, feature-rich native IDE for FoxVC."""

    def __init__(self, root: Any, initial_file: str = None):
        if not HAS_TKINTER:
            raise RuntimeError(
                "Fox Den Studio desktop GUI requires Tkinter, which is not available in this environment. "
                "Use 'foxvc studio --web' to run the Web Studio or install python3-tk."
            )
        self.root = root
        self.documents = []
        self.active_doc_idx = -1
        self.active_stage_window = None
        self.active_spatial_scene = None
        self.compiler = StandaloneCompiler()

        self._init_window()
        self._setup_theme()
        self._build_header_deck()
        self._build_keyword_ribbon()
        self._build_editor_workspace()
        self._build_bottom_multi_drawer()
        self._bind_shortcuts()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.open_folder_path(base_dir)

        if initial_file and os.path.exists(initial_file):
            abs_p = os.path.abspath(initial_file)
            if os.path.isfile(abs_p):
                self.open_file_path(abs_p)
            else:
                self.new_file()
        else:
            sample = os.path.join(base_dir, "examples", "hero_tic_tac_toe.fox")
            if os.path.exists(sample):
                self.open_file_path(sample)
            else:
                self.new_file()

    def _init_window(self):
        self.root.title(f"🦊 Fox Den Studio — Engine v{rt.FOXVC_ENGINE_VERSION} (Lang v{rt.FOXVC_LANGUAGE_VERSION})")
        self.root.geometry("1240x860")
        self.root.minsize(880, 600)
        self.root.configure(bg="#08080C")

    def _setup_theme(self):
        self.c_bg = "#08080C"
        self.c_panel = "#100F15"
        self.c_card = "#14131B"
        self.c_border = "#262232"
        self.c_accent = "#FF7A00"
        self.c_accent_glow = "#FFA048"
        self.c_cyan = "#38BDF8"
        self.c_green = "#10B981"
        self.c_text = "#EDE8E1"
        self.c_muted = "#7A7085"

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=self.c_panel, foreground="#D4CCC3", fieldbackground=self.c_panel, borderwidth=0, font=("DejaVu Sans", 9))
        style.map("Treeview", background=[("selected", "#3D2618")], foreground=[("selected", "#FFA94D")])

    def _build_header_deck(self):
        """Top Command Deck with Brand, Mode Selector, Action Controls, and Presets."""
        header = tk.Frame(self.root, bg=self.c_panel, height=50, bd=0, highlightthickness=1, highlightbackground=self.c_border)
        header.pack(fill=tk.X, side=tk.TOP)

        # Brand & Status Pill
        left = tk.Frame(header, bg=self.c_panel)
        left.pack(side=tk.LEFT, padx=14, pady=8)

        tk.Label(left, text="🦊 FOX DEN STUDIO", bg=self.c_panel, fg=self.c_accent, font=("DejaVu Sans", 11, "bold")).pack(side=tk.LEFT)
        self.engine_badge = tk.Label(left, text=f"⚡ Engine v{rt.FOXVC_ENGINE_VERSION} [CVM-Ready]", bg="#1C1824", fg=self.c_cyan, font=("DejaVu Sans", 8, "bold"), padx=10, pady=3)
        self.engine_badge.pack(side=tk.LEFT, padx=12)

        # Action Buttons
        right = tk.Frame(header, bg=self.c_panel)
        right.pack(side=tk.RIGHT, padx=14, pady=8)

        def btn(txt, cmd, bg_col=None, fg_col="#FFFFFF"):
            bg = bg_col or "#1D1A27"
            return tk.Button(right, text=txt, command=cmd, bg=bg, fg=fg_col, activebackground="#FF9124", activeforeground="#FFF", bd=0, padx=11, pady=4, font=("DejaVu Sans", 8, "bold"), cursor="hand2")

        btn("▶ RUN (F5)", self.run_code, bg_col=self.c_accent).pack(side=tk.RIGHT, padx=3)
        btn("🔍 AUDIT (F6)", self.run_diagnostics, bg_col="#252136", fg_col=self.c_cyan).pack(side=tk.RIGHT, padx=3)
        btn("🧹 FMT (F4)", self.format_active_code, bg_col="#1C2420", fg_col="#34D399").pack(side=tk.RIGHT, padx=3)
        btn("🧪 TEST (F10)", self.run_tests, bg_col="#2B2024", fg_col="#FB7185").pack(side=tk.RIGHT, padx=3)
        btn("⚡ BUILD BINARY (F8)", self.build_standalone_binary, bg_col="#1B3128", fg_col=self.c_green).pack(side=tk.RIGHT, padx=3)
        btn("🌀 3D STAGE (F9)", self.launch_3d_stage, bg_col="#291F38", fg_col="#C084FC").pack(side=tk.RIGHT, padx=3)
        btn("🌐 WEB (F7)", self.launch_web_app).pack(side=tk.RIGHT, padx=3)

        # Presets Dropdown
        self.preset_var = tk.StringVar(value="Load Preset...")
        presets = [
            "Preset: Starter FoxVC",
            "Preset: 3D Rotating Mesh Routine",
            "Preset: Micro HTTP Server & API",
            "Preset: Autonomous Tic-Tac-Toe Arena",
            "Preset: Fibonacci VM Benchmark"
        ]
        self.preset_menu = ttk.Combobox(right, textvariable=self.preset_var, values=presets, state="readonly", width=22)
        self.preset_menu.pack(side=tk.RIGHT, padx=6)
        self.preset_menu.bind("<<ComboboxSelected>>", self._on_preset_selected)

    def _build_keyword_ribbon(self):
        """Quick-Insert Ribbon containing the 25 official FoxVC keywords."""
        ribbon = tk.Frame(self.root, bg="#0B0A10", height=32, bd=0, highlightthickness=1, highlightbackground=self.c_border)
        ribbon.pack(fill=tk.X, side=tk.TOP)

        tk.Label(ribbon, text="25 KEYWORDS:", bg="#0B0A10", fg=self.c_muted, font=("DejaVu Sans", 7, "bold"), padx=10).pack(side=tk.LEFT)

        keywords = [
            ("lock", "#FF7A00"), ("shift", "#FF7A00"), ("blank", "#FF7A00"),
            ("act", "#38BDF8"), ("emit", "#38BDF8"),
            ("pick", "#A78BFA"), ("alt", "#A78BFA"), ("otherwise", "#A78BFA"),
            ("spin", "#34D399"), ("pulse", "#34D399"), ("cycle", "#34D399"), ("halt", "#F87171"), ("skip", "#F87171"),
            ("say", "#FBBF24"), ("ask", "#FBBF24"),
            ("guard", "#F43F5E"), ("trap", "#F43F5E"), ("fuse", "#F43F5E"),
            ("pack", "#818CF8"), ("mold", "#818CF8"),
            ("aye", "#10B981"), ("nay", "#F43F5E"), ("also", "#38BDF8"), ("either", "#38BDF8"), ("deny", "#F43F5E")
        ]

        for kw, col in keywords:
            lbl = tk.Label(ribbon, text=kw, bg="#13111C", fg=col, font=("Monospace", 8, "bold"), padx=6, pady=2, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2, pady=4)
            lbl.bind("<Button-1>", lambda e, word=kw: self.insert_keyword(word))

    def insert_keyword(self, word: str):
        self.editor.insert(tk.INSERT, f"{word} ")
        self.editor.focus_set()
        self._on_key_release()

    def _build_editor_workspace(self):
        self.h_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.c_border, bd=0, sashwidth=4)
        self.h_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 0))

        # Project Explorer
        self.sidebar_frame = tk.Frame(self.h_paned, bg=self.c_panel, width=220)
        self.sidebar_frame.pack_propagate(False)

        side_header = tk.Frame(self.sidebar_frame, bg="#0C0B12", height=30)
        side_header.pack(fill=tk.X)
        self.side_title = tk.Label(side_header, text="WORKSPACE EXPLORER", bg="#0C0B12", fg=self.c_muted, font=("DejaVu Sans", 8, "bold"), padx=10, pady=6)
        self.side_title.pack(side=tk.LEFT)

        self.file_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.file_tree.bind("<Double-1>", self._on_tree_click)
        self.h_paned.add(self.sidebar_frame, minsize=150)

        # Editor Pane
        editor_pane = tk.Frame(self.h_paned, bg=self.c_bg)

        self.tab_strip = tk.Frame(editor_pane, bg="#121019", height=32)
        self.tab_strip.pack(fill=tk.X)
        self.tab_strip.pack_propagate(False)

        editor_body = tk.Frame(editor_pane, bg=self.c_card)
        editor_body.pack(fill=tk.BOTH, expand=True)

        self.lines = LineNumbers(editor_body, None)
        self.lines.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(
            editor_body,
            bg=self.c_card,
            fg=self.c_text,
            insertbackground=self.c_accent,
            selectbackground="#4D2A18",
            selectforeground="#FFFFFF",
            font=("Monospace", 10),
            bd=0,
            undo=True,
            padx=14,
            pady=10
        )
        self.lines.text_widget = self.editor
        self.editor.pack(fill=tk.BOTH, expand=True)
        self._configure_syntax_tags()

        self.h_paned.add(editor_pane, minsize=520)

    def _build_bottom_multi_drawer(self):
        """Bottom Multi-Drawer with Console, Bytecode Inspector, and Native Deploy tabs."""
        self.drawer_frame = tk.Frame(self.root, bg=self.c_panel, height=240, bd=0, highlightthickness=1, highlightbackground=self.c_border)
        self.drawer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(4, 10))
        self.drawer_frame.pack_propagate(False)

        # Drawer Tab Bar
        tab_bar = tk.Frame(self.drawer_frame, bg="#0C0B12", height=30)
        tab_bar.pack(fill=tk.X)

        self.drawer_tab = "console"
        self.btn_tab_console = tk.Button(tab_bar, text="🖥 Console & Diagnostics", command=lambda: self.switch_drawer_tab("console"), bg="#1C1827", fg=self.c_accent, bd=0, padx=12, font=("DejaVu Sans", 8, "bold"), cursor="hand2")
        self.btn_tab_console.pack(side=tk.LEFT)

        self.btn_tab_bytecode = tk.Button(tab_bar, text="⚙ Bytecode Disassembler", command=lambda: self.switch_drawer_tab("bytecode"), bg="#0C0B12", fg=self.c_muted, bd=0, padx=12, font=("DejaVu Sans", 8, "bold"), cursor="hand2")
        self.btn_tab_bytecode.pack(side=tk.LEFT)

        self.btn_tab_deploy = tk.Button(tab_bar, text="🚀 Native Deployment & CLI", command=lambda: self.switch_drawer_tab("deploy"), bg="#0C0B12", fg=self.c_muted, bd=0, padx=12, font=("DejaVu Sans", 8, "bold"), cursor="hand2")
        self.btn_tab_deploy.pack(side=tk.LEFT)

        tk.Button(tab_bar, text="Clear", command=self.clear_output, bg="#0C0B12", fg=self.c_muted, bd=0, padx=8, font=("DejaVu Sans", 8), cursor="hand2").pack(side=tk.RIGHT)

        # Drawer Body Container
        self.drawer_body = tk.Frame(self.drawer_frame, bg="#0A090E")
        self.drawer_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        scrollbar = tk.Scrollbar(self.drawer_body, bg="#121019")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.out_text = tk.Text(self.drawer_body, bg="#0A090E", fg=self.c_text, font=("Monospace", 9), bd=0, padx=10, pady=6, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.out_text.yview)
        self.out_text.pack(fill=tk.BOTH, expand=True)

        self.out_text.tag_configure("badge_pass", background="#15803D", foreground="#FFFFFF", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("badge_fail", background="#B91C1C", foreground="#FFFFFF", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("badge_blocked", background="#CA8A04", foreground="#000000", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("accent", foreground=self.c_accent, font=("DejaVu Sans", 9, "bold"))
        self.out_text.tag_configure("cyan", foreground=self.c_cyan, font=("DejaVu Sans", 9, "bold"))
        self.out_text.tag_configure("green", foreground=self.c_green, font=("DejaVu Sans", 9, "bold"))
        self.out_text.tag_configure("muted", foreground="#786F85")
        self.out_text.tag_configure("err", foreground="#F87171")

    def switch_drawer_tab(self, tab: str):
        self.drawer_tab = tab
        self.btn_tab_console.config(bg="#1C1827" if tab == "console" else "#0C0B12", fg=self.c_accent if tab == "console" else self.c_muted)
        self.btn_tab_bytecode.config(bg="#1C1827" if tab == "bytecode" else "#0C0B12", fg=self.c_cyan if tab == "bytecode" else self.c_muted)
        self.btn_tab_deploy.config(bg="#1C1827" if tab == "deploy" else "#0C0B12", fg=self.c_green if tab == "deploy" else self.c_muted)

        if tab == "bytecode":
            self.disassemble_bytecode()
        elif tab == "deploy":
            self.show_deployment_info()

    def show_deployment_info(self):
        self.out_text.delete("1.0", tk.END)
        self.out_text.insert(tk.END, "🦊 FOXVC NATIVE ENGINE DEPLOYMENT & CLI\n\n", "accent")
        self.out_text.insert(tk.END, "To run native microservices, hardware-accelerated 3D graphics, or raw sockets:\n\n")

        self.out_text.insert(tk.END, "1. Universal One-Line Installer (Linux & macOS):\n", "cyan")
        self.out_text.insert(tk.END, "   curl -sSL https://raw.githubusercontent.com/AnayUpadhyay-all/FoxVC/main/install.sh | bash\n\n")

        self.out_text.insert(tk.END, "2. Android Termux Native Installation:\n", "cyan")
        self.out_text.insert(tk.END, "   pkg install -y clang git python make\n")
        self.out_text.insert(tk.END, "   curl -sSL https://raw.githubusercontent.com/AnayUpadhyay-all/FoxVC/main/install.sh | bash\n\n")

        self.out_text.insert(tk.END, "3. Standalone Binary Compilation (Zero-Dependency C Binary):\n", "green")
        self.out_text.insert(tk.END, "   foxvc build main.fox -o myapp\n")
        self.out_text.insert(tk.END, "   ./myapp\n\n")

        compiler_path = self.compiler.find_c_compiler()
        comp_str = f"Detected: {compiler_path[0]} ({compiler_path[1]})" if compiler_path else "No C compiler found in PATH"
        self.out_text.insert(tk.END, f"Host C Toolchain: {comp_str}\n", "muted")

    def disassemble_bytecode(self):
        doc = self.get_active_doc()
        if not doc:
            return
        code = self.editor.get("1.0", tk.END)
        self.out_text.delete("1.0", tk.END)
        self.out_text.insert(tk.END, f"FOXVM BYTECODE DISASSEMBLY — {doc.title}\n\n", "cyan")

        try:
            tokens = Lexer(code).tokenize()
            ast = Parser(tokens).parse()
            comp = BytecodeCompiler()
            bytecode_data = comp.compile(ast)
            instructions = bytecode_data[0] if isinstance(bytecode_data, tuple) else bytecode_data

            self.out_text.insert(tk.END, f"Instruction Stream ({len(instructions)} opcodes):\n", "muted")
            for idx, inst in enumerate(instructions):
                self.out_text.insert(tk.END, f"  [{idx:04d}] ", "muted")
                if isinstance(inst, tuple):
                    op_name = str(inst[0]).replace("Op.", "")
                    args = ", ".join(repr(a) for a in inst[1:])
                    self.out_text.insert(tk.END, f"{op_name:<16} ", "accent")
                    self.out_text.insert(tk.END, f"{args}\n")
                else:
                    self.out_text.insert(tk.END, f"{inst}\n")

            if isinstance(bytecode_data, tuple) and len(bytecode_data) >= 3:
                self.out_text.insert(tk.END, f"\nConstants Pool: {len(bytecode_data[1])} numbers, {len(bytecode_data[2])} strings\n", "muted")

        except Exception as e:
            self.out_text.insert(tk.END, f"Disassembly Error: {e}\n", "err")

    def build_standalone_binary(self, event=None):
        doc = self.get_active_doc()
        if not doc:
            return
        self.save_file()
        if not doc.filepath:
            messagebox.showwarning("Save Required", "Please save your script to a file before compiling to binary.")
            return

        self.switch_drawer_tab("console")
        self.clear_output()
        self.out_text.insert(tk.END, f"COMPILING STANDALONE BINARY — {doc.title}\n\n", "green")

        base_name = os.path.splitext(doc.filepath)[0]
        out_bin = f"{base_name}_app" if sys.platform != "win32" else f"{base_name}.exe"

        try:
            res = self.compiler.build(doc.filepath, output_path=out_bin)
            if res.success:
                kb_size = res.binary_size_bytes / 1024.0
                self.out_text.insert(tk.END, f"✓ COMPILATION SUCCESSFUL\n", "green")
                self.out_text.insert(tk.END, f"  Executable Binary: {res.output_path}\n")
                self.out_text.insert(tk.END, f"  Size on Disk:      {kb_size:.1f} KB (Zero-dependency C binary)\n")
                self.out_text.insert(tk.END, f"  Compiler Tool:     {res.compiler_used}\n")
                self.out_text.insert(tk.END, f"  Bytecode Size:     {res.bytecode_len} instructions\n\n")
                self.out_text.insert(tk.END, f"To execute: ./{os.path.basename(res.output_path)}\n", "cyan")
            else:
                self.out_text.insert(tk.END, f"✗ BUILD FAILED:\n\n{res.error}\n", "err")
        except Exception as e:
            self.out_text.insert(tk.END, f"✗ BUILD ERROR: {e}\n", "err")

    def launch_3d_stage(self, event=None):
        if self.active_stage_window and self.active_stage_window.winfo_exists():
            self.active_stage_window.lift()
            return
        self.active_stage_window = Stage3DWindow(self.root, scene=self.active_spatial_scene)

    def _configure_syntax_tags(self):
        self.editor.tag_configure("kw", foreground=self.c_accent, font=("Monospace", 10, "bold"))
        self.editor.tag_configure("builtin_kw", foreground=self.c_cyan, font=("Monospace", 10, "bold"))
        self.editor.tag_configure("num", foreground="#F59E0B")
        self.editor.tag_configure("str", foreground="#86EFAC")
        self.editor.tag_configure("comment", foreground="#5E566A", font=("Monospace", 10, "italic"))

    def _apply_syntax_highlighting(self):
        code = self.editor.get("1.0", tk.END)
        for tag in ("kw", "builtin_kw", "num", "str", "comment"):
            self.editor.tag_remove(tag, "1.0", tk.END)

        fox_keywords = r"\b(act|emit|pack|mold|pick|alt|otherwise|pulse|cycle|spin|halt|skip|say|ask|guard|trap|fuse|lock|shift|blank|aye|nay|also|either|deny)\b"
        builtin_names = r"\b(push|pop|remove_at|sin|cos|sqrt|rnd|time|len|str|int|float|shelf|math|system|file|crypto|net|db|graphics)\b"

        for m in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"', code):
            self.editor.tag_add("str", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(r"\b\d+(?:\.\d+)?\b", code):
            self.editor.tag_add("num", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(fox_keywords, code):
            self.editor.tag_add("kw", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(builtin_names, code):
            self.editor.tag_add("builtin_kw", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(r"(?:#|//)[^\n]*", code):
            self.editor.tag_add("comment", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

    def _bind_shortcuts(self):
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<F4>", lambda e: self.format_active_code())
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<F6>", lambda e: self.run_diagnostics())
        self.root.bind("<F7>", lambda e: self.launch_web_app())
        self.root.bind("<F8>", lambda e: self.build_standalone_binary())
        self.root.bind("<F9>", lambda e: self.launch_3d_stage())
        self.root.bind("<F10>", lambda e: self.run_tests())

    def format_active_code(self, event=None):
        doc = self.get_active_doc()
        if not doc:
            return
        code = self.editor.get("1.0", tk.END)
        formatter = FoxFormatter()
        formatted = formatter.format_source(code)
        if formatted != code:
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", formatted)
            doc.is_modified = True
            doc.content = formatted
            self.update_tab_bar()
            self.lines.redraw()
            self._apply_syntax_highlighting()
        self.switch_drawer_tab("console")
        self.out_text.insert(tk.END, "✓ Document formatted cleanly (canonical 4-space indentation).\n", "green")

    def run_tests(self, event=None):
        doc = self.get_active_doc()
        if not doc:
            return
        self.save_file()
        runner = FoxTestRunner()
        self.switch_drawer_tab("console")
        self.clear_output()
        self.out_text.insert(tk.END, f"FOXVC TEST SUITE AUDIT — {doc.title}\n\n", "accent")
        results = runner.run_file_suite(doc.filepath) if doc.filepath else []
        if not results:
            self.out_text.insert(tk.END, "No test functions (act test_*) found in document.\n", "muted")
            return
        passed_c, failed_c = 0, 0
        for r in results:
            tag = "badge_pass" if r.passed else "badge_fail"
            txt = "PASS" if r.passed else "FAIL"
            self.out_text.insert(tk.END, f" {txt} ", tag)
            self.out_text.insert(tk.END, f"  {r.test_name} ({r.duration_ms:.2f}ms)\n")
            if r.passed:
                passed_c += 1
            else:
                failed_c += 1
                if r.error_message:
                    self.out_text.insert(tk.END, f"       ↳ {r.error_message}\n", "err")
        self.out_text.insert(tk.END, f"\nTest Summary: {passed_c} Passed | {failed_c} Failed\n", "green" if failed_c == 0 else "err")

    def _on_key_release(self, event=None):
        doc = self.get_active_doc()
        if doc:
            doc.is_modified = True
            doc.content = self.editor.get("1.0", tk.END)
        self.lines.redraw()
        self._apply_syntax_highlighting()

    def get_active_doc(self):
        if 0 <= self.active_doc_idx < len(self.documents):
            return self.documents[self.active_doc_idx]
        return None

    def update_tab_bar(self):
        for w in self.tab_strip.winfo_children():
            w.destroy()
        for idx, doc in enumerate(self.documents):
            active = (idx == self.active_doc_idx)
            bg = "#231F30" if active else "#121019"
            fg = self.c_accent if active else "#8A8197"
            tab = tk.Frame(self.tab_strip, bg=bg, padx=8, pady=3)
            tab.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))

            dot = "● " if doc.is_modified else ""
            lbl = tk.Label(tab, text=f"{dot}{doc.title}", bg=bg, fg=fg, font=("DejaVu Sans", 8, "bold" if active else "normal"))
            lbl.pack(side=tk.LEFT, padx=(3, 5))
            lbl.bind("<Button-1>", lambda e, i=idx: self.switch_tab(i))

            close_btn = tk.Label(tab, text="✕", bg=bg, fg="#6A6178", font=("DejaVu Sans", 7))
            close_btn.pack(side=tk.RIGHT, padx=(1, 3))
            close_btn.bind("<Button-1>", lambda e, i=idx: self.close_tab(i))

    def switch_tab(self, idx):
        if idx < 0 or idx >= len(self.documents):
            return
        cur = self.get_active_doc()
        if cur:
            cur.content = self.editor.get("1.0", tk.END)

        self.active_doc_idx = idx
        doc = self.documents[idx]
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", doc.content)
        self.update_tab_bar()
        self.lines.redraw()
        self._apply_syntax_highlighting()

    def close_tab(self, idx):
        if idx < 0 or idx >= len(self.documents):
            return
        del self.documents[idx]
        if not self.documents:
            self.new_file()
        else:
            self.switch_tab(max(0, idx - 1))

    def new_file(self):
        starter = (
            "// FoxVC Starter Program\n"
            "lock greeting = \"Welcome to Fox Den Studio!\"\n"
            "say greeting\n\n"
            "act calculate(a, b) {\n"
            "    lock sum = a + b\n"
            "    emit sum\n"
            "}\n\n"
            "lock total = calculate(15, 27)\n"
            "say \"Result: \" + total\n"
        )
        doc = DocumentTab(filepath=None, title="untitled.fox", content=starter)
        self.documents.append(doc)
        self.switch_tab(len(self.documents) - 1)

    def _on_preset_selected(self, event=None):
        val = self.preset_var.get()
        if "3D Rotating" in val:
            content = (
                "// FoxVC 3D Spatial Geometry Matrix & Rotating Mesh\n"
                "say \"=== FoxVC 3D Spatial Geometry Matrix ===\";\n"
                "say \"Target: 60 FPS Trigonometric Transform Pipeline\";\n\n"
                "act project_point(x, y, z, angle) {\n"
                "    // Isometric trigonometric rotation\n"
                "    lock rx = x * 0.866 - z * 0.500;\n"
                "    lock rz = x * 0.500 + z * 0.866;\n"
                "    lock fov = 260 / (rz + 300);\n"
                "    lock sx = 300 + (rx * fov);\n"
                "    emit sx;\n"
                "}\n\n"
                "shift vertex_idx = 0;\n"
                "spin (vertex_idx < 8) {\n"
                "    lock screen_x = project_point(40, -40, 40, 0.785);\n"
                "    say \"Projected Vertex [\" + vertex_idx + \"] Screen X: \" + screen_x;\n"
                "    vertex_idx = vertex_idx + 1;\n"
                "}\n"
                "say \"Execution clean. Press [F9] to view live 60 FPS 3D Rotating Stage!\";\n"
            )
            title = "mesh_3d.fox"
        elif "HTTP Server" in val:
            content = (
                "// FoxVC Micro Backend Server & API Gateway\n"
                "lock PORT = 8080;\n"
                "say \"=== Initializing FoxVC Micro HTTP Server on Port \" + PORT + \" ===\";\n"
                "fuse net;\n"
                "fuse system;\n\n"
                "act handle_route(method, endpoint) {\n"
                "    pick (endpoint == \"/health\") {\n"
                "        alt aye: emit \"{ 'status': 'pass', 'engine': 'foxvm_c', 'port': 8080 }\";\n"
                "        otherwise: emit \"{ 'error': '404 Not Found' }\";\n"
                "    }\n"
                "}\n\n"
                "say \"Server routes registered:\";\n"
                "say \"  GET  /health       -> System Status Probe\";\n"
                "say \"  POST /api/v1/data  -> Fast Ingest Queue\";\n"
                "say \"Server loop ready. Press [F8] to compile standalone binary (foxvc build)!\";\n"
            )
            title = "server.fox"
        elif "Tic-Tac-Toe" in val:
            examples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
            hero_fp = os.path.join(examples_dir, "hero_tic_tac_toe.fox")
            if os.path.exists(hero_fp):
                self.open_file_path(hero_fp)
                return
            content = "// Tic Tac Toe Arena\nsay \"Tic-Tac-Toe Arena Ready\";\n"
            title = "tic_tac_toe.fox"
        elif "Fibonacci" in val:
            content = (
                "// FoxVC Fibonacci Benchmark\n"
                "act fib(n) {\n"
                "    pick (n <= 1) {\n"
                "        alt aye: emit n;\n"
                "    }\n"
                "    emit fib(n - 1) + fib(n - 2);\n"
                "}\n\n"
                "say \"Computing Fibonacci(20)...\";\n"
                "lock res = fib(20);\n"
                "say \"Result: \" + res;\n"
            )
            title = "fibonacci.fox"
        else:
            self.new_file()
            return

        doc = DocumentTab(filepath=None, title=title, content=content)
        self.documents.append(doc)
        self.switch_tab(len(self.documents) - 1)

    def open_file_dialog(self):
        fp = filedialog.askopenfilename()
        if fp:
            self.open_file_path(os.path.abspath(fp))

    def open_file_path(self, fp):
        for idx, doc in enumerate(self.documents):
            if doc.filepath and os.path.abspath(doc.filepath) == os.path.abspath(fp):
                self.switch_tab(idx)
                return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                code = f.read()
            doc = DocumentTab(filepath=fp, title=os.path.basename(fp), content=code)
            self.documents.append(doc)
            self.switch_tab(len(self.documents) - 1)
        except Exception as e:
            messagebox.showerror("FoxVC Error", str(e))

    def open_folder_path(self, folder):
        self.side_title.config(text=f"📁 {os.path.basename(folder).upper()}")
        self.file_tree.delete(*self.file_tree.get_children())
        self._populate_tree("", folder)

    def _populate_tree(self, parent, path):
        try:
            items = sorted(os.listdir(path))
        except Exception:
            return
        for i in items:
            if i.startswith(".") or i == "__pycache__":
                continue
            fp = os.path.join(path, i)
            if os.path.isdir(fp):
                node = self.file_tree.insert(parent, "end", text=f"📁 {i}", values=[fp, "dir"])
                self._populate_tree(node, fp)
            else:
                icon = "🦊" if i.endswith((".fox", ".foxc")) else "📄"
                self.file_tree.insert(parent, "end", text=f"{icon} {i}", values=[fp, "file"])

    def _on_tree_click(self, event=None):
        sel = self.file_tree.selection()
        if not sel:
            return
        vals = self.file_tree.item(sel[0], "values")
        if vals and len(vals) >= 2 and vals[1] == "file":
            self.open_file_path(vals[0])

    def save_file(self):
        doc = self.get_active_doc()
        if not doc:
            return
        if not doc.filepath:
            doc.filepath = filedialog.asksaveasfilename(initialfile=doc.title)
        if doc.filepath:
            with open(doc.filepath, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", tk.END))
            doc.is_modified = False
            self.update_tab_bar()

    def clear_output(self):
        self.out_text.delete("1.0", tk.END)

    def run_code(self, event=None):
        doc = self.get_active_doc()
        if not doc:
            return
        source = self.editor.get("1.0", tk.END)

        self.switch_drawer_tab("console")
        self.clear_output()

        # Check for Native Network Server usage
        is_server_code = bool(re.search(r"\b(fuse\s+(net|server|socket)|PORT\s*=|listen|serve)\b", source))
        if is_server_code:
            self.out_text.insert(tk.END, "⚡ NATIVE BACKEND SERVER SCRIPT DETECTED\n", "accent")
            self.out_text.insert(tk.END, "Host TCP socket binding and system daemon threads are active.\n", "cyan")
            self.out_text.insert(tk.END, "To compile into a standalone server daemon with zero Python runtime, press [F8].\n\n", "muted")

        res = run_foxvc(source, file_path=doc.filepath)

        if res.success:
            self.out_text.insert(tk.END, "✓ EXECUTION SUCCESSFUL\n", "green")
            if res.output:
                self.out_text.insert(tk.END, res.output + "\n")

            # Check if 3D Mesh / spatial scene is requested
            is_3d_code = bool(re.search(r"\b(project_point|mesh|3D|Spatial|vertices)\b", source, re.IGNORECASE))
            if is_3d_code:
                self.out_text.insert(tk.END, "\n• 3D Spatial Geometry detected! Press [F9] to view live rotating geometry.\n", "cyan")

            # Launch/Update Stage window if explicit scene is returned
            scene = getattr(res, "spatial_space", None) or res.metadata.get("spatial_space")
            if scene:
                self.active_spatial_scene = scene
                self.launch_3d_stage()
        else:
            self.out_text.insert(tk.END, f"✗ RUNTIME ERROR:\n\n{res.error}\n", "err")

    def run_diagnostics(self, event=None):
        doc = self.get_active_doc()
        if not doc:
            return
        source = self.editor.get("1.0", tk.END)
        res = run_foxvc_diagnostic(source, file_path=doc.filepath)

        self.switch_drawer_tab("console")
        self.clear_output()
        self.out_text.insert(tk.END, "FOXVC STATEMENT DIAGNOSTIC AUDIT\n\n", "accent")

        reports = getattr(res, "statement_reports", [])
        if not reports and isinstance(res, list):
            reports = res

        pass_c, fail_c, block_c = 0, 0, 0
        for r in reports:
            line_no = getattr(r, "line", 1)
            status = getattr(r, "status", "PASS")
            src = getattr(r, "source", "")

            badge_tag = "badge_pass"
            if status == "FAIL":
                badge_tag = "badge_fail"
                fail_c += 1
            elif status == "BLOCKED":
                badge_tag = "badge_blocked"
                block_c += 1
            else:
                pass_c += 1

            self.out_text.insert(tk.END, f"[{line_no:02d}] ", "muted")
            self.out_text.insert(tk.END, f" {status} ", badge_tag)
            self.out_text.insert(tk.END, f"  {src}\n")

            diag_obj = getattr(r, "diagnostic", None)
            if diag_obj:
                msg = getattr(diag_obj, "message", str(diag_obj))
                self.out_text.insert(tk.END, f"      ↳ {msg}\n", "err")

        self.out_text.insert(tk.END, f"\nAudit Summary: {pass_c} Passed | {fail_c} Failed | {block_c} Blocked\n", "muted")

    def launch_web_app(self, event=None):
        messagebox.showinfo("FoxVC Web Studio", "Launch Web Studio via command line:\npython3 run_web.py\n\nOr on mobile via:\nfoxvc mobile")


def main():
    if not HAS_TKINTER:
        print("Error: Fox Den Studio desktop GUI requires Tkinter, which is not available in this environment.")
        print("Run 'foxvc studio --web' to launch the Web Studio or install python3-tk.")
        sys.exit(1)
    root = tk.Tk()
    app = FoxVCStudio(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()


if __name__ == "__main__":
    main()
