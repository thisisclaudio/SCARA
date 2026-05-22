#!/usr/bin/env python3
"""
SCARA GUI Launcher
Startet application/main.py mit einer gewählten YAML-Datei.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import os
import sys
import glob
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY    = os.path.join(SCRIPT_DIR, "application", "main.py")
APP_DIR    = os.path.join(SCRIPT_DIR, "application")

# ── Farben ──────────────────────────────────────────────────────────────────
BG       = "#0f0f14"
SURFACE  = "#18181f"
SURFACE2 = "#22222d"
BORDER   = "#2e2e3d"
ACCENT   = "#e94560"
ACCENT2  = "#7c5cbf"
TEXT     = "#e8e8f0"
MUTED    = "#6b6b80"
SUCCESS  = "#3ddc84"
WARNING  = "#f5a623"
DANGER   = "#ff4f5e"

FONT_MONO = ("Courier New", 10)
FONT_UI   = ("Helvetica", 11)
FONT_SM   = ("Helvetica", 10)
FONT_LG   = ("Helvetica", 14, "bold")


def count_steps(yaml_path: str) -> int:
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return len(data.get("program", []))
    except Exception:
        return 0


class ScaraGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SCARA — Program Runner")
        self.geometry("760x580")
        self.minsize(640, 500)
        self.configure(bg=BG)

        self._process   = None
        self._running   = False
        self._stop_flag = threading.Event()
        self._total_steps = 0
        self._done_steps  = 0

        self._style()
        self._build()
        self._load_yaml_files()

    # ── ttk style ──────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox",
                    fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, selectbackground=ACCENT2,
                    selectforeground=TEXT, bordercolor=BORDER,
                    arrowcolor=ACCENT, padding=8)
        s.map("TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              foreground=[("readonly", TEXT)])
        s.configure("Bar.Horizontal.TProgressbar",
                    troughcolor=SURFACE2, bordercolor=SURFACE2,
                    background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    thickness=8)

    # ── UI aufbauen ────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬡  SCARA", font=("Courier New", 16, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="Program Runner", font=FONT_SM,
                 bg=SURFACE, fg=MUTED).pack(side="left")

        # Trennlinie
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # Mittelbereich
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="both", expand=True, padx=20, pady=16)

        # ── Auswahl-Card
        card1 = self._card(mid)
        card1.pack(fill="x", pady=(0, 12))

        tk.Label(card1, text="YAML-Programm auswählen", font=FONT_SM,
                 bg=SURFACE, fg=MUTED).pack(anchor="w", padx=16, pady=(12, 4))

        row = tk.Frame(card1, bg=SURFACE)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self._yaml_var = tk.StringVar()
        self._combo = ttk.Combobox(row, textvariable=self._yaml_var,
                                   state="readonly", font=FONT_UI)
        self._combo.pack(side="left", fill="x", expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._on_yaml_select)

        tk.Button(row, text="↺", font=("Helvetica", 13),
                  bg=SURFACE2, fg=MUTED, activebackground=BORDER,
                  activeforeground=TEXT, relief="flat", bd=0, padx=10,
                  cursor="hand2", command=self._load_yaml_files
                  ).pack(side="left", padx=(8, 0))

        # ── Info-Zeile (Schritte)
        self._info_lbl = tk.Label(card1, text="", font=FONT_SM,
                                  bg=SURFACE, fg=MUTED)
        self._info_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # ── Fortschritts-Card
        card2 = self._card(mid)
        card2.pack(fill="x", pady=(0, 12))

        hrow = tk.Frame(card2, bg=SURFACE)
        hrow.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hrow, text="Fortschritt", font=FONT_SM,
                 bg=SURFACE, fg=MUTED).pack(side="left")
        self._pct_lbl = tk.Label(hrow, text="—", font=FONT_SM,
                                 bg=SURFACE, fg=TEXT)
        self._pct_lbl.pack(side="right")

        self._progress = ttk.Progressbar(card2, style="Bar.Horizontal.TProgressbar",
                                         mode="determinate", maximum=100)
        self._progress.pack(fill="x", padx=16, pady=(0, 8))

        self._status_lbl = tk.Label(card2, text="Bereit", font=FONT_SM,
                                    bg=SURFACE, fg=SUCCESS)
        self._status_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # ── Buttons
        btn_row = tk.Frame(mid, bg=BG)
        btn_row.pack(fill="x", pady=(0, 12))

        self._run_btn = tk.Button(
            btn_row, text="▶  Programm starten",
            font=("Helvetica", 12, "bold"),
            bg=ACCENT, fg="white",
            activebackground="#c73550", activeforeground="white",
            relief="flat", bd=0, padx=20, pady=10,
            cursor="hand2", command=self._run
        )
        self._run_btn.pack(side="left")

        self._stop_btn = tk.Button(
            btn_row, text="■  Stop",
            font=("Helvetica", 12),
            bg=SURFACE2, fg=DANGER,
            activebackground=BORDER, activeforeground=DANGER,
            relief="flat", bd=0, padx=20, pady=10,
            cursor="hand2", state="disabled",
            command=self._stop
        )
        self._stop_btn.pack(side="left", padx=(10, 0))

        # ── Konsolen-Log
        log_lbl = tk.Label(mid, text="Ausgabe", font=FONT_SM, bg=BG, fg=MUTED)
        log_lbl.pack(anchor="w", pady=(4, 4))

        self._log = tk.Text(
            mid, bg=SURFACE, fg=TEXT, font=FONT_MONO,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT2,
            insertbackground=TEXT, state="disabled",
            wrap="word", height=10
        )
        self._log.pack(fill="both", expand=True)

        sb = tk.Scrollbar(self._log, command=self._log.yview,
                          bg=SURFACE2, troughcolor=SURFACE)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Tag-Farben für Logs
        self._log.tag_configure("ok",   foreground=SUCCESS)
        self._log.tag_configure("err",  foreground=DANGER)
        self._log.tag_configure("warn", foreground=WARNING)
        self._log.tag_configure("info", foreground=MUTED)
        self._log.tag_configure("step", foreground=ACCENT2)

    def _card(self, parent):
        f = tk.Frame(parent, bg=SURFACE, bd=1, relief="flat",
                     highlightbackground=BORDER, highlightthickness=1)
        return f

    # ── YAML laden ─────────────────────────────────────────────────────────
    def _load_yaml_files(self):
        files = sorted(glob.glob(os.path.join(APP_DIR, "*.yaml")))
        names = [os.path.basename(f) for f in files]
        self._yaml_files = {n: p for n, p in zip(names, files)}
        self._combo["values"] = names
        if names:
            self._combo.current(0)
            self._on_yaml_select()
        else:
            self._log_write("Keine .yaml-Dateien in application/ gefunden.", "err")

    def _on_yaml_select(self, *_):
        name = self._yaml_var.get()
        path = self._yaml_files.get(name, "")
        n = count_steps(path)
        self._total_steps = n
        self._info_lbl.config(text=f"{n} Schritt{'e' if n != 1 else ''} gefunden")

    # ── Run / Stop ─────────────────────────────────────────────────────────
    def _run(self):
        name = self._yaml_var.get()
        if not name or name not in self._yaml_files:
            self._log_write("Bitte zuerst eine YAML-Datei auswählen.", "err")
            return

        yaml_path = self._yaml_files[name]
        self._running = True
        self._stop_flag.clear()
        self._done_steps = 0
        self._progress["value"] = 0
        self._pct_lbl.config(text="0 %")
        self._clear_log()
        self._set_status("Läuft…", WARNING)
        self._run_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._combo.config(state="disabled")

        self._log_write(f"▶ Starte: {name}\n", "ok")
        t = threading.Thread(target=self._worker, args=(yaml_path,), daemon=True)
        t.start()

    def _stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._log_write("\n■ Programm gestoppt.\n", "err")
        self._stop_flag.set()
        self._finish(aborted=True)

    def _worker(self, yaml_path):
        try:
            self._process = subprocess.Popen(
                [sys.executable, MAIN_PY, yaml_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=SCRIPT_DIR
            )
            for line in self._process.stdout:
                if self._stop_flag.is_set():
                    break
                self.after(0, self._handle_line, line)

            self._process.wait()
            if not self._stop_flag.is_set():
                self.after(0, self._finish, False)
        except Exception as e:
            self.after(0, self._log_write, f"Fehler: {e}\n", "err")
            self.after(0, self._finish, True)

    def _handle_line(self, line: str):
        line = line.rstrip("\n")
        tag = "info"
        low = line.lower()
        if "moving" in low or "setting" in low:
            tag = "step"
            self._done_steps += 1
            if self._total_steps > 0:
                pct = int(min(self._done_steps / self._total_steps * 100, 100))
                self._progress["value"] = pct
                self._pct_lbl.config(text=f"{pct} %")
        elif "error" in low or "exception" in low or "traceback" in low:
            tag = "err"
        elif "warning" in low or "warn" in low:
            tag = "warn"
        elif "waiting" in low:
            tag = "info"
        else:
            tag = "ok"
        self._log_write(line + "\n", tag)

    def _finish(self, aborted: bool):
        self._running = False
        self._run_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._combo.config(state="readonly")
        if aborted:
            self._progress["value"] = 0
            self._pct_lbl.config(text="—")
            self._set_status("Gestoppt", DANGER)
        else:
            self._progress["value"] = 100
            self._pct_lbl.config(text="100 %")
            self._set_status("Fertig ✓", SUCCESS)
            self._log_write("\n✓ Programm abgeschlossen.\n", "ok")

    # ── Hilfsmethoden ──────────────────────────────────────────────────────
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


if __name__ == "__main__":
    app = ScaraGUI()
    app.mainloop()