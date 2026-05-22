#!/usr/bin/env python3
"""
SCARA GUI — wird von main.py gestartet.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import glob
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# ── Farben ──────────────────────────────────────────────────────────────────
BG       = "#0f0f14"
SURFACE  = "#18181f"
SURFACE2 = "#22222d"
BORDER   = "#2e2e3d"
ACCENT   = "#e94560"
TEXT     = "#e8e8f0"
MUTED    = "#6b6b80"
SUCCESS  = "#3ddc84"
WARNING  = "#f5a623"
DANGER   = "#ff4f5e"
PURPLE   = "#7c5cbf"

MONO = ("Courier New", 10)
UI   = ("Helvetica", 11)
SM   = ("Helvetica", 10)
LG   = ("Helvetica", 13, "bold")


def count_steps(yaml_path) -> int:
    from yaml_parser import parse
    try:
        return len(parse(str(yaml_path)))
    except Exception:
        return 0


class ScaraApp(tk.Tk):
    def __init__(self, robot, run_fn):
        """
        robot  : bereits initialisiertes Robot-Objekt
        run_fn : run(program_file, robot, log_callback) aus main.py
        """
        super().__init__()
        self._robot   = robot
        self._run_fn  = run_fn
        self._running = False
        self._abort   = threading.Event()
        self._total_steps = 0
        self._done_steps  = 0

        self.title("SCARA — Robot Controller")
        self.geometry("740x600")
        self.minsize(620, 520)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._style_setup()
        self._build_ui()
        self._load_yaml_list()

        self.after(100, self._on_robot_ready)

    # ── ttk-Styles ─────────────────────────────────────────────────────────
    def _style_setup(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("C.TCombobox",
                    fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, selectbackground=PURPLE,
                    selectforeground=TEXT, bordercolor=BORDER,
                    arrowcolor=ACCENT, padding=8)
        s.map("C.TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              foreground=[("readonly", TEXT)])
        s.configure("C.Horizontal.TProgressbar",
                    troughcolor=SURFACE2, bordercolor=SURFACE2,
                    background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    thickness=10)

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬡  SCARA", font=("Courier New", 15, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=20)
        self._conn_dot = tk.Label(hdr, text="●", font=SM, bg=SURFACE, fg=WARNING)
        self._conn_dot.pack(side="right", padx=6)
        self._conn_lbl = tk.Label(hdr, text="Verbinde…", font=SM, bg=SURFACE, fg=MUTED)
        self._conn_lbl.pack(side="right")
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # ── Programmauswahl
        c1 = self._card(body)
        c1.pack(fill="x", pady=(0, 10))
        tk.Label(c1, text="Programm", font=SM, bg=SURFACE, fg=MUTED
                 ).pack(anchor="w", padx=14, pady=(12, 4))

        row = tk.Frame(c1, bg=SURFACE)
        row.pack(fill="x", padx=14, pady=(0, 10))
        self._yaml_var = tk.StringVar()
        self._combo = ttk.Combobox(row, textvariable=self._yaml_var,
                                   state="readonly", style="C.TCombobox", font=UI)
        self._combo.pack(side="left", fill="x", expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._on_select)
        tk.Button(row, text="↺", font=("Helvetica", 13), bg=SURFACE2,
                  fg=MUTED, activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", bd=0, padx=10, cursor="hand2",
                  command=self._load_yaml_list).pack(side="left", padx=(8, 0))

        self._step_lbl = tk.Label(c1, text="", font=SM, bg=SURFACE, fg=MUTED)
        self._step_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # ── Fortschritt
        c2 = self._card(body)
        c2.pack(fill="x", pady=(0, 10))
        top = tk.Frame(c2, bg=SURFACE)
        top.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(top, text="Fortschritt", font=SM, bg=SURFACE, fg=MUTED).pack(side="left")
        self._pct_lbl = tk.Label(top, text="—", font=SM, bg=SURFACE, fg=TEXT)
        self._pct_lbl.pack(side="right")
        self._bar = ttk.Progressbar(c2, style="C.Horizontal.TProgressbar",
                                    mode="determinate", maximum=100)
        self._bar.pack(fill="x", padx=14, pady=(0, 8))
        self._status_lbl = tk.Label(c2, text="Warte auf Roboter…", font=SM,
                                    bg=SURFACE, fg=WARNING)
        self._status_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # ── Buttons
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x", pady=(0, 10))
        self._run_btn = tk.Button(
            btn_row, text="▶  Starten", font=LG,
            bg=ACCENT, fg="white", activebackground="#c73550",
            activeforeground="white", relief="flat", bd=0,
            padx=22, pady=10, cursor="hand2",
            state="disabled", command=self._start_program)
        self._run_btn.pack(side="left")
        self._stop_btn = tk.Button(
            btn_row, text="■  Stop", font=("Helvetica", 12),
            bg=SURFACE2, fg=DANGER, activebackground=BORDER,
            activeforeground=DANGER, relief="flat", bd=0,
            padx=22, pady=10, cursor="hand2",
            state="disabled", command=self._stop_program)
        self._stop_btn.pack(side="left", padx=(10, 0))

        # ── Log
        tk.Label(body, text="Ausgabe", font=SM, bg=BG, fg=MUTED
                 ).pack(anchor="w", pady=(4, 4))
        log_frame = tk.Frame(body, bg=SURFACE,
                             highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self._log = tk.Text(log_frame, bg=SURFACE, fg=TEXT, font=MONO,
                            relief="flat", bd=0, state="disabled",
                            wrap="word", insertbackground=TEXT)
        sb = tk.Scrollbar(log_frame, command=self._log.yview,
                          bg=SURFACE2, troughcolor=SURFACE, relief="flat")
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=4, pady=4)

        self._log.tag_configure("ok",   foreground=SUCCESS)
        self._log.tag_configure("err",  foreground=DANGER)
        self._log.tag_configure("warn", foreground=WARNING)
        self._log.tag_configure("info", foreground=MUTED)
        self._log.tag_configure("step", foreground=PURPLE)
        self._log.tag_configure("sys",  foreground=ACCENT)

    def _card(self, parent):
        return tk.Frame(parent, bg=SURFACE,
                        highlightbackground=BORDER, highlightthickness=1)

    # ── Robot bereit ────────────────────────────────────────────────────────
    def _on_robot_ready(self):
        self._log_write("✓ Roboter verbunden und bereit.\n", "ok")
        self._conn_dot.config(fg=SUCCESS)
        self._conn_lbl.config(text="Verbunden", fg=SUCCESS)
        self._set_status("Bereit", SUCCESS)
        self._run_btn.config(state="normal")

    # ── YAML-Liste ──────────────────────────────────────────────────────────
    def _load_yaml_list(self):
        files = sorted(glob.glob(str(APP_DIR / "*.yaml")))
        self._yaml_map = {Path(f).name: f for f in files}
        names = list(self._yaml_map.keys())
        self._combo["values"] = names
        if names:
            self._combo.current(0)
            self._on_select()
        else:
            self._log_write("Keine .yaml-Dateien in application/ gefunden.\n", "err")

    def _on_select(self, *_):
        name = self._yaml_var.get()
        path = self._yaml_map.get(name, "")
        n = count_steps(path)
        self._total_steps = n
        self._step_lbl.config(text=f"{n} Schritt{'e' if n != 1 else ''}")

    # ── Starten / Stoppen ───────────────────────────────────────────────────
    def _start_program(self):
        name = self._yaml_var.get()
        if not name:
            messagebox.showerror("Fehler", "Bitte ein Programm auswählen.")
            return

        yaml_path = self._yaml_map[name]
        self._running = True
        self._abort.clear()
        self._done_steps = 0
        self._bar["value"] = 0
        self._pct_lbl.config(text="0 %")
        self._clear_log()
        self._set_status("Läuft…", WARNING)
        self._run_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._combo.config(state="disabled")
        self._log_write(f"▶ Starte: {name}\n\n", "sys")

        threading.Thread(target=self._worker, args=(yaml_path,), daemon=True).start()

    def _worker(self, yaml_path: str):
        try:
            self._run_fn(
                yaml_path,
                self._robot,
                log_callback=lambda msg: self.after(0, self._on_step, msg)
            )
            if not self._abort.is_set():
                self.after(0, self._finish, False)
        except Exception as e:
            self.after(0, self._log_write, f"\n✗ Fehler: {e}\n", "err")
            self.after(0, self._finish, True)

    def _on_step(self, msg: str):
        low = msg.lower()
        if any(k in low for k in ("movej", "movel", "gripper →", "wait →")):
            tag = "step"
            self._done_steps += 1
            if self._total_steps > 0:
                pct = int(min(self._done_steps / self._total_steps * 100, 100))
                self._bar["value"] = pct
                self._pct_lbl.config(text=f"{pct} %")
        elif "fehler" in low or "error" in low:
            tag = "err"
        else:
            tag = "info"
        self._log_write(msg + "\n", tag)

    def _stop_program(self):
        self._abort.set()
        self._log_write("\n■ Programm abgebrochen.\n", "err")
        self._finish(aborted=True)

    def _finish(self, aborted: bool):
        self._running = False
        self._run_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._combo.config(state="readonly")
        if aborted:
            self._bar["value"] = 0
            self._pct_lbl.config(text="—")
            self._set_status("Gestoppt", DANGER)
        else:
            self._bar["value"] = 100
            self._pct_lbl.config(text="100 %")
            self._set_status("Fertig ✓", SUCCESS)
            self._log_write("\n✓ Programm abgeschlossen.\n", "ok")

    # ── Schliessen ──────────────────────────────────────────────────────────
    def _on_close(self):
        if self._running:
            if not messagebox.askyesno("Beenden",
                    "Ein Programm läuft noch. Trotzdem beenden?"):
                return
            self._abort.set()
        self._log_write("\nFahre Roboter herunter…\n", "sys")
        self.update()
        try:
            self._robot.shutdown()
        except Exception as e:
            print(f"Shutdown-Fehler: {e}")
        self.destroy()

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _set_status(self, text, color):
        self._status_lbl.config(text=text, fg=color)

    def _log_write(self, text, tag="info"):
        self._log.config(state="normal")
        self._log.insert("end", text, tag)
        self._log.see("end")
        self._log.config(state="disabled")

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")