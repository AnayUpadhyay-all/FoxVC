"""
FoxVC Desktop Studio (Permanent Master Edition)
Pure-Decoupled IDE: Distraction-free Editor, Complete Diagnostic Inspector,
and Standalone 60 FPS 2D Pop-Up Stage Window.
"""

import os
import sys
import time
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import engine.runtime as rt
from engine.runner import run_foxvc, run_foxvc_diagnostic
from engine.web import FoxWebRuntime

class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.configure(width=46, bg="#0E0D0C", highlightthickness=0, bd=0)

    def redraw(self):
        self.delete("all")
        if not self.text_widget: return
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0].zfill(2)
            self.create_text(34, y + 4, anchor="ne", text=linenum, fill="#4A433D", font=("Monospace", 9))
            i = self.text_widget.index(f"{i}+1line")

class DocumentTab:
    def __init__(self, filepath=None, title="untitled.fox", content=""):
        self.filepath = filepath
        self.title = title
        self.is_modified = False
        self.content = content

class Stage2DWindow(tk.Toplevel):
    """Standalone 60 FPS 2D Pop-Up Visual Stage Window."""
    def __init__(self, parent, scene, svg_content=""):
        super().__init__(parent)
        self.scene = scene
        self.svg_content = svg_content
        self.title(f"🦊 FoxVC 2D Stage — {getattr(scene, 'name', 'Visual World')}")
        self.geometry("900x700")
        self.minsize(500, 400)
        self.configure(bg="#05060A")
        
        self.is_paused = False
        self.start_time = time.time()
        self.pause_offset = 0.0

        # Toolbar
        bar = tk.Frame(self, bg="#0A0C13", height=36)
        bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(bar, text=f"🌌 {getattr(scene, 'name', 'World')}", bg="#0A0C13", fg="#38BDF8", font=("DejaVu Sans", 9, "bold")).pack(side=tk.LEFT, padx=12, pady=6)
        self.fps_lbl = tk.Label(bar, text="60 FPS", bg="#0A0C13", fg="#64748B", font=("DejaVu Sans", 8))
        self.fps_lbl.pack(side=tk.LEFT, padx=6)

        tk.Button(bar, text="💾 Save SVG", command=self.save_svg, bg="#161A24", fg="#38BDF8", bd=0, padx=10, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2").pack(side=tk.RIGHT, padx=6)
        self.btn_pause = tk.Button(bar, text="⏸ Pause", command=self.toggle_pause, bg="#161A24", fg="#E2E8F0", bd=0, padx=10, pady=2, font=("DejaVu Sans", 8, "bold"), cursor="hand2")
        self.btn_pause.pack(side=tk.RIGHT, padx=4)

        # Drawing Canvas
        self.canvas = tk.Canvas(self, bg=getattr(scene, "background", "#05060A"), bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._start_render_loop()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.config(text="▶ Play" if self.is_paused else "⏸ Pause")

    def save_svg(self):
        if not self.svg_content:
            self.svg_content = getattr(self.scene, "to_svg", lambda: "")()
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("Vector SVG", "*.svg"), ("All Files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.svg_content)
            messagebox.showinfo("Export", f"Vector SVG saved:\n{path}")

    def _start_render_loop(self):
        def loop():
            if self.winfo_exists():
                if not self.is_paused:
                    t = time.time() - self.start_time
                    cw = self.canvas.winfo_width() or 600
                    ch = self.canvas.winfo_height() or 500
                    
                    if hasattr(self.scene, "render_frame_to_canvas"):
                        self.scene.render_frame_to_canvas(self.canvas, cw, ch, t)
                    elif hasattr(self.scene, "render_to_canvas"):
                        self.scene.render_to_canvas(self.canvas, cw, ch)
                    elif hasattr(self.scene, "render"):
                        self.scene.render(self.canvas, cw, ch)

                self.after(16, loop)
        self.after(50, loop)

class FoxVCStudio:
    def __init__(self, root: tk.Tk, initial_file: str = None):
        self.root = root
        self.documents = []
        self.active_doc_idx = -1
        self.active_spatial_scene = None
        self.last_export_svg = ""
        self.active_stage_window = None

        self._init_window()
        self._setup_theme()
        self._build_topbar()
        self._build_editor_stage()
        self._build_diagnostic_drawer()
        self._bind_shortcuts()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.open_folder_path(base_dir)

        if initial_file and os.path.exists(initial_file):
            abs_p = os.path.abspath(initial_file)
            if os.path.isfile(abs_p): self.open_file_path(abs_p)
            else: self.new_file()
        else:
            sample = os.path.join(base_dir, "examples", "KinematicSolarSystem.fox")
            if os.path.exists(sample): self.open_file_path(sample)
            else: self.new_file()

    def _init_window(self):
        self.root.title(f"FoxVC Studio — Engine v{rt.FOXVC_LANGUAGE_VERSION}")
        self.root.geometry("1160x820")
        self.root.minsize(840, 580)
        self.root.configure(bg="#080707")

    def _setup_theme(self):
        self.c_bg = "#080707"
        self.c_surface = "#110F0E"
        self.c_card = "#161412"
        self.c_border = "#24201C"
        self.c_accent = "#FF7A00"
        self.c_text = "#EDE8E1"
        self.c_muted = "#7A7067"

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=self.c_surface, foreground="#D4CCC3", fieldbackground=self.c_surface, borderwidth=0, font=("DejaVu Sans", 9))
        style.map("Treeview", background=[("selected", "#38291D")], foreground=[("selected", "#FFA94D")])

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg="#0E0D0C", height=46, bd=0, highlightthickness=1, highlightbackground=self.c_border)
        bar.pack(fill=tk.X, side=tk.TOP)

        left = tk.Frame(bar, bg="#0E0D0C")
        left.pack(side=tk.LEFT, padx=14, pady=8)

        tk.Label(left, text="🦊 FOXVC STUDIO", bg="#0E0D0C", fg=self.c_accent, font=("DejaVu Sans", 11, "bold")).pack(side=tk.LEFT)
        self.doc_badge = tk.Label(left, text="• Ready", bg="#1C1815", fg="#A89E93", font=("DejaVu Sans", 8, "bold"), padx=10, pady=3)
        self.doc_badge.pack(side=tk.LEFT, padx=12)

        right = tk.Frame(bar, bg="#0E0D0C")
        right.pack(side=tk.RIGHT, padx=14, pady=8)

        def btn(txt, cmd, highlight=False):
            bg = self.c_accent if highlight else "#181614"
            fg = "#FFFFFF" if highlight else "#D4CCC1"
            return tk.Button(right, text=txt, command=cmd, bg=bg, fg=fg, activebackground="#FF9124", activeforeground="#FFF", bd=0, padx=12, pady=4, font=("DejaVu Sans", 8, "bold"), cursor="hand2")

        btn("RUN (F5)", self.run_code, highlight=True).pack(side=tk.RIGHT, padx=3)
        btn("DIAGNOSE (F6)", self.run_diagnostics).pack(side=tk.RIGHT, padx=3)
        btn("LAUNCH WEB (F7)", self.launch_web_app).pack(side=tk.RIGHT, padx=3)
        btn("Save", self.save_file).pack(side=tk.RIGHT, padx=3)
        btn("Open", self.open_file_dialog).pack(side=tk.RIGHT, padx=3)
        btn("New", self.new_file).pack(side=tk.RIGHT, padx=3)

    def _build_editor_stage(self):
        self.h_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.c_border, bd=0, sashwidth=4)
        self.h_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 0))

        # Project Explorer
        self.sidebar_frame = tk.Frame(self.h_paned, bg=self.c_surface, width=220)
        self.sidebar_frame.pack_propagate(False)

        side_header = tk.Frame(self.sidebar_frame, bg="#0C0A09", height=28)
        side_header.pack(fill=tk.X)
        self.side_title = tk.Label(side_header, text="WORKSPACE", bg="#0C0A09", fg=self.c_muted, font=("DejaVu Sans", 8, "bold"), padx=10, pady=5)
        self.side_title.pack(side=tk.LEFT)

        self.file_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.file_tree.bind("<Double-1>", self._on_tree_click)
        self.h_paned.add(self.sidebar_frame, minsize=140)

        # Editor Frame
        editor_pane = tk.Frame(self.h_paned, bg=self.c_bg)
        
        self.tab_strip = tk.Frame(editor_pane, bg="#110F0E", height=30)
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
            selectbackground="#4D331D",
            selectforeground="#FFFFFF",
            font=("Monospace", 10),
            bd=0,
            undo=True,
            padx=12,
            pady=8
        )
        self.lines.text_widget = self.editor
        self.editor.pack(fill=tk.BOTH, expand=True)
        self._configure_syntax_tags()

        self.h_paned.add(editor_pane, minsize=500)

    def _build_diagnostic_drawer(self):
        self.drawer_frame = tk.Frame(self.root, bg=self.c_surface, height=210, bd=0, highlightthickness=1, highlightbackground=self.c_border)
        self.drawer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(4, 10))
        self.drawer_frame.pack_propagate(False)

        drawer_top = tk.Frame(self.drawer_frame, bg="#0D0B0A", height=28)
        drawer_top.pack(fill=tk.X)

        self.drawer_label = tk.Label(drawer_top, text="🔍 DIAGNOSTIC AUDITOR & OUTPUT", bg="#0D0B0A", fg=self.c_muted, font=("DejaVu Sans", 8, "bold"), padx=10, pady=5)
        self.drawer_label.pack(side=tk.LEFT)

        tk.Button(drawer_top, text="Clear", command=self.clear_output, bg="#0D0B0A", fg=self.c_muted, activebackground="#1C1815", bd=0, padx=8, font=("DejaVu Sans", 8), cursor="hand2").pack(side=tk.RIGHT)

        out_body = tk.Frame(self.drawer_frame, bg="#0D0C0B")
        out_body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        scrollbar = tk.Scrollbar(out_body, bg="#110F0E")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.out_text = tk.Text(out_body, bg="#0D0C0B", fg=self.c_text, font=("Monospace", 9), bd=0, padx=10, pady=6, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.out_text.yview)
        self.out_text.pack(fill=tk.BOTH, expand=True)

        self.out_text.tag_configure("badge_pass", background="#15803D", foreground="#FFFFFF", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("badge_fail", background="#B91C1C", foreground="#FFFFFF", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("badge_blocked", background="#CA8A04", foreground="#000000", font=("DejaVu Sans", 7, "bold"))
        self.out_text.tag_configure("accent", foreground=self.c_accent, font=("DejaVu Sans", 9, "bold"))
        self.out_text.tag_configure("muted", foreground="#786F66")
        self.out_text.tag_configure("err", foreground="#F87171")

    def _configure_syntax_tags(self):
        self.editor.tag_configure("kw", foreground=self.c_accent, font=("Monospace", 10, "bold"))
        self.editor.tag_configure("spatial_kw", foreground="#38BDF8", font=("Monospace", 10, "bold"))
        self.editor.tag_configure("num", foreground="#F59E0B")
        self.editor.tag_configure("str", foreground="#86EFAC")
        self.editor.tag_configure("comment", foreground="#5E564F", font=("Monospace", 10, "italic"))

    def _apply_syntax_highlighting(self):
        code = self.editor.get("1.0", tk.END)
        for tag in ("kw", "spatial_kw", "num", "str", "comment"):
            self.editor.tag_remove(tag, "1.0", tk.END)

        spatial_keywords = r"\b(space|entity|form|anchor|anchored_to|inside|beside|around|aligned|replicate|connect|span|distributed|period|orbit|pulse|spin|wave|phase|cycle|linear|radial|field)\b"
        core_keywords = r"\b(say|ask|set|add|render|bind|mount|element|use|skin|apply|action|state|fetch|timer|navigate|store|hide|show|enable|disable|remove|true|false|and|or|not)\b"

        for m in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"', code):
            self.editor.tag_add("str", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(r"\b\d+(?:\.\d+)?\b", code):
            self.editor.tag_add("num", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(core_keywords, code, re.IGNORECASE):
            self.editor.tag_add("kw", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(spatial_keywords, code, re.IGNORECASE):
            self.editor.tag_add("spatial_kw", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        for m in re.finditer(r"#[^\n]*", code):
            self.editor.tag_add("comment", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

    def _bind_shortcuts(self):
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<F6>", lambda e: self.run_diagnostics())
        self.root.bind("<F7>", lambda e: self.launch_web_app())

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
        for w in self.tab_strip.winfo_children(): w.destroy()
        for idx, doc in enumerate(self.documents):
            active = (idx == self.active_doc_idx)
            bg = "#1E1A17" if active else "#110F0E"
            fg = self.c_accent if active else "#8A8177"
            tab = tk.Frame(self.tab_strip, bg=bg, padx=8, pady=3)
            tab.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))

            dot = "● " if doc.is_modified else ""
            lbl = tk.Label(tab, text=f"{dot}{doc.title}", bg=bg, fg=fg, font=("DejaVu Sans", 8, "bold" if active else "normal"))
            lbl.pack(side=tk.LEFT, padx=(3, 5))
            lbl.bind("<Button-1>", lambda e, i=idx: self.switch_tab(i))

            close_btn = tk.Label(tab, text="✕", bg=bg, fg="#5E564F", font=("DejaVu Sans", 7))
            close_btn.pack(side=tk.RIGHT, padx=(1, 3))
            close_btn.bind("<Button-1>", lambda e, i=idx: self.close_tab(i))

    def switch_tab(self, idx):
        if idx < 0 or idx >= len(self.documents): return
        cur = self.get_active_doc()
        if cur: cur.content = self.editor.get("1.0", tk.END)

        self.active_doc_idx = idx
        doc = self.documents[idx]
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", doc.content)
        self.doc_badge.config(text=f"🦊 {doc.title}")
        self.update_tab_bar()
        self.lines.redraw()
        self._apply_syntax_highlighting()

    def close_tab(self, idx):
        if idx < 0 or idx >= len(self.documents): return
        del self.documents[idx]
        if not self.documents: self.new_file()
        else: self.switch_tab(max(0, idx - 1))

    def new_file(self):
        doc = DocumentTab(filepath=None, title="world.fox", content='space NewVisualWorld\n    background "#080B12"\n\n    entity Core\n        form circle\n        diameter 80\n        fill "#FF7A00"\n        pulse min 0.9 max 1.1 period 2.0\n\n    entity Satellite\n        form circle\n        diameter 20\n        fill "#38BDF8"\n        around Core distance 150 period 4.0\n')
        self.documents.append(doc)
        self.switch_tab(len(self.documents) - 1)

    def open_file_dialog(self):
        fp = filedialog.askopenfilename()
        if fp: self.open_file_path(os.path.abspath(fp))

    def open_file_path(self, fp):
        for idx, doc in enumerate(self.documents):
            if doc.filepath and os.path.abspath(doc.filepath) == os.path.abspath(fp):
                self.switch_tab(idx)
                return
        try:
            with open(fp, "r", encoding="utf-8") as f: code = f.read()
            doc = DocumentTab(filepath=fp, title=os.path.basename(fp), content=code)
            self.documents.append(doc)
            self.switch_tab(len(self.documents) - 1)
        except Exception as e:
            messagebox.showerror("FoxVC Error", str(e))

    def open_folder_dialog(self):
        folder = filedialog.askdirectory()
        if folder: self.open_folder_path(os.path.abspath(folder))

    def open_folder_path(self, folder):
        self.side_title.config(text=f"📁 {os.path.basename(folder).upper()}")
        self.file_tree.delete(*self.file_tree.get_children())
        self._populate_tree("", folder)

    def _populate_tree(self, parent, path):
        try: items = sorted(os.listdir(path))
        except Exception: return
        for i in items:
            if i.startswith(".") or i == "__pycache__": continue
            fp = os.path.join(path, i)
            if os.path.isdir(fp):
                node = self.file_tree.insert(parent, "end", text=f"📁 {i}", values=[fp, "dir"])
                self._populate_tree(node, fp)
            else:
                icon = "🦊" if i.endswith((".fox", ".fweb", ".fskin", ".flogic")) else "📄"
                self.file_tree.insert(parent, "end", text=f"{icon} {i}", values=[fp, "file"])

    def _on_tree_click(self, event=None):
        sel = self.file_tree.selection()
        if not sel: return
        vals = self.file_tree.item(sel[0], "values")
        if vals and len(vals) >= 2 and vals[1] == "file":
            self.open_file_path(vals[0])

    def save_file(self):
        doc = self.get_active_doc()
        if not doc: return
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
        if not doc: return
        source = self.editor.get("1.0", tk.END)
        res = run_foxvc(source, file_path=doc.filepath)

        self.clear_output()
        if res.success:
            self.out_text.insert(tk.END, "✓ EXECUTION SUCCESSFUL\n", "accent")
            if res.output:
                self.out_text.insert(tk.END, res.output + "\n")

            # Check for 2D Spatial Scene
            scene = getattr(res, "spatial_space", None) or res.metadata.get("spatial_space")
            if scene:
                self.active_spatial_scene = scene
                self.last_export_svg = getattr(res, "svg_output", "") or res.metadata.get("svg_output", "")
                self.out_text.insert(tk.END, f"\n• Launching 2D Pop-Up Stage Window: {getattr(scene, 'name', 'World')} ({len(scene.entities)} Entities)\n", "muted")
                
                # Close prior pop-up if open
                if self.active_stage_window and self.active_stage_window.winfo_exists():
                    self.active_stage_window.destroy()

                # Launch standalone stage window
                self.active_stage_window = Stage2DWindow(self.root, scene, self.last_export_svg)
        else:
            self.out_text.insert(tk.END, f"✗ RUNTIME ERROR:\n\n{res.error}\n", "err")

    def run_diagnostics(self, event=None):
        doc = self.get_active_doc()
        if not doc: return
        source = self.editor.get("1.0", tk.END)
        res = run_foxvc_diagnostic(source, file_path=doc.filepath)

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
        doc = self.get_active_doc()
        if not doc: return
        res = run_foxvc(self.editor.get("1.0", tk.END), file_path=doc.filepath)
        if res.success and getattr(res, "is_web_app", False):
            FoxWebRuntime.launch(res.web_app)
        else:
            messagebox.showinfo("FoxVC Web", "No mounted WebApplication found. Use 'mount app' or write an .fweb application.")

def main():
    root = tk.Tk()
    app = FoxVCStudio(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()

if __name__ == "__main__":
    main()
