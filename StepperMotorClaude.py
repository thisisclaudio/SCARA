#!/usr/bin/env python3
"""
Stepper UART Controller – Demo GUI
Steuert zwei Schrittmotoren über serielle JSON-Schnittstelle.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import json
import threading
import time
import queue


# ─────────────────────────────────────────────
#  Konfiguration
# ─────────────────────────────────────────────
BAUDRATE = 115200

AXIS1_MAX = 2500
AXIS2_MAX = 58000

HOME_CMD = {
    1: {"id": 1, "cmd": "home", "speed": 300,  "accel": 6000},
    2: {"id": 2, "cmd": "home", "speed": 6000, "accel": 60000},
}

COLORS = {
    "bg":        "#0f1117",
    "panel":     "#1a1d27",
    "border":    "#2a2d3e",
    "accent1":   "#00d4ff",   # Cyan – Achse 1
    "accent2":   "#ff6b35",   # Orange – Achse 2
    "text":      "#e2e8f0",
    "text_dim":  "#64748b",
    "ok":        "#22c55e",
    "error":     "#ef4444",
    "warn":      "#f59e0b",
    "btn_bg":    "#252836",
    "btn_hover": "#2e3247",
}


# ─────────────────────────────────────────────
#  Serial-Manager (Thread-safe)
# ─────────────────────────────────────────────
class SerialManager:
    def __init__(self):
        self.ser: serial.Serial | None = None
        self.lock = threading.Lock()
        self.rx_queue: queue.Queue = queue.Queue()
        self._rx_thread: threading.Thread | None = None
        self._running = False

    def connect(self, port: str, baudrate: int = BAUDRATE) -> bool:
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.5)
            self._running = True
            self._rx_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._rx_thread.start()
            return True
        except Exception as e:
            print(f"[Serial] Verbindungsfehler: {e}")
            return False

    def disconnect(self):
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None

    def send(self, obj: dict):
        if not self.ser or not self.ser.is_open:
            return
        payload = json.dumps(obj, separators=(',', ':')) + '\n'
        with self.lock:
            self.ser.write(payload.encode('utf-8'))

    def _read_loop(self):
        while self._running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        try:
                            self.rx_queue.put(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass
            time.sleep(0.01)

    @property
    def connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    @staticmethod
    def list_ports() -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]


# ─────────────────────────────────────────────
#  COM-Port Auswahl Dialog
# ─────────────────────────────────────────────
class PortDialog(tk.Toplevel):
    def __init__(self, parent, ports: list[str]):
        super().__init__(parent)
        self.result: str | None = None
        self.title("COM-Port auswählen")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.grab_set()

        # Zentrieren
        self.update_idletasks()
        pw, ph = 380, 260
        x = parent.winfo_x() + (parent.winfo_width()  - pw) // 2
        y = parent.winfo_y() + (parent.winfo_height() - ph) // 2
        self.geometry(f"{pw}x{ph}+{x}+{y}")

        tk.Label(self, text="⚡  Stepper Controller",
                 font=("Courier New", 14, "bold"),
                 fg=COLORS["accent1"], bg=COLORS["bg"]).pack(pady=(22, 4))

        tk.Label(self, text="Verfügbare COM-Ports:",
                 font=("Courier New", 9),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack()

        frame = tk.Frame(self, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame.pack(padx=24, pady=10, fill="x")

        self.var = tk.StringVar(value=ports[0] if ports else "")
        for p in ports:
            tk.Radiobutton(frame, text=p, variable=self.var, value=p,
                           font=("Courier New", 10),
                           fg=COLORS["text"], bg=COLORS["panel"],
                           activebackground=COLORS["panel"],
                           selectcolor=COLORS["bg"],
                           relief="flat").pack(anchor="w", padx=14, pady=3)

        if not ports:
            tk.Label(frame, text="Keine Ports gefunden",
                     font=("Courier New", 9),
                     fg=COLORS["error"], bg=COLORS["panel"]).pack(pady=8)

        btn_frame = tk.Frame(self, bg=COLORS["bg"])
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="Verbinden",
                  font=("Courier New", 10, "bold"),
                  bg=COLORS["accent1"], fg=COLORS["bg"],
                  activebackground="#00b8d9",
                  relief="flat", bd=0, padx=18, pady=6,
                  cursor="hand2",
                  command=self._connect,
                  state="normal" if ports else "disabled").pack(side="left", padx=6)

        tk.Button(btn_frame, text="Abbrechen",
                  font=("Courier New", 10),
                  bg=COLORS["btn_bg"], fg=COLORS["text_dim"],
                  activebackground=COLORS["btn_hover"],
                  relief="flat", bd=0, padx=18, pady=6,
                  cursor="hand2",
                  command=self.destroy).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _connect(self):
        self.result = self.var.get()
        self.destroy()


# ─────────────────────────────────────────────
#  Achsen-Panel
# ─────────────────────────────────────────────
class AxisPanel(tk.Frame):
    def __init__(self, parent, axis_id: int, label: str,
                 max_pos: int, accent: str,
                 send_cb, **kwargs):
        super().__init__(parent, bg=COLORS["panel"],
                         highlightbackground=accent,
                         highlightthickness=2, **kwargs)

        self.axis_id   = axis_id
        self.max_pos   = max_pos
        self.accent    = accent
        self.send_cb   = send_cb
        self._homing   = False
        self._actual_pos = 0      # Ist-Position vom Controller
        self._target_pos = 0      # Sollwert vom Slider
        self._dragging   = False  # True während Slider gezogen wird

        # ── Header ──────────────────────────────
        hdr = tk.Frame(self, bg=accent)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"  {label}",
                 font=("Courier New", 12, "bold"),
                 fg=COLORS["bg"], bg=accent,
                 anchor="w").pack(side="left", fill="x", expand=True, pady=6)

        self.status_dot = tk.Label(hdr, text="●",
                                   font=("Courier New", 12),
                                   fg=COLORS["bg"], bg=accent)
        self.status_dot.pack(side="right", padx=10)

        # ── Body ────────────────────────────────
        body = tk.Frame(self, bg=COLORS["panel"])
        body.pack(fill="x", padx=14, pady=12)

        # Linke Spalte: Homing
        left = tk.Frame(body, bg=COLORS["panel"])
        left.pack(side="left", padx=(0, 16))

        tk.Label(left, text="HOMING",
                 font=("Courier New", 7, "bold"),
                 fg=COLORS["text_dim"], bg=COLORS["panel"]).pack()

        self.home_btn = tk.Button(
            left,
            text="⌂\nHOME",
            font=("Courier New", 11, "bold"),
            fg=accent, bg=COLORS["btn_bg"],
            activebackground=COLORS["btn_hover"],
            activeforeground=accent,
            relief="flat", bd=0,
            width=5, height=3,
            cursor="hand2",
            command=self._do_home
        )
        self.home_btn.pack()

        self.homed_label = tk.Label(left,
                                    text="—",
                                    font=("Courier New", 7),
                                    fg=COLORS["text_dim"],
                                    bg=COLORS["panel"])
        self.homed_label.pack(pady=(4, 0))

        # Rechte Spalte
        right = tk.Frame(body, bg=COLORS["panel"])
        right.pack(side="left", fill="x", expand=True)

        # ── Zeile 1: SOLL-Wert (Slider) ─────────
        soll_hdr = tk.Frame(right, bg=COLORS["panel"])
        soll_hdr.pack(fill="x", pady=(0, 2))

        tk.Label(soll_hdr, text="SOLL",
                 font=("Courier New", 7, "bold"),
                 fg=COLORS["text_dim"], bg=COLORS["panel"],
                 anchor="w").pack(side="left")

        self.target_label = tk.Label(soll_hdr,
                                     text="0",
                                     font=("Courier New", 11, "bold"),
                                     fg=accent, bg=COLORS["panel"],
                                     anchor="e")
        self.target_label.pack(side="right")

        self.slider_var = tk.IntVar(value=0)
        self.slider = ttk.Scale(
            right,
            from_=0, to=max_pos,
            orient="horizontal",
            variable=self.slider_var,
            command=self._on_slider_move
        )
        self.slider.pack(fill="x", pady=(0, 2))
        # Maus-Events: Senden erst beim Loslassen
        self.slider.bind("<ButtonPress-1>",   self._slider_press)
        self.slider.bind("<ButtonRelease-1>", self._slider_release)

        # ── Zeile 2: IST-Position (Canvas-Balken) ─
        ist_hdr = tk.Frame(right, bg=COLORS["panel"])
        ist_hdr.pack(fill="x", pady=(6, 2))

        tk.Label(ist_hdr, text="IST",
                 font=("Courier New", 7, "bold"),
                 fg=COLORS["text_dim"], bg=COLORS["panel"],
                 anchor="w").pack(side="left")

        self.pos_label = tk.Label(ist_hdr,
                                  text="—",
                                  font=("Courier New", 11, "bold"),
                                  fg=COLORS["ok"], bg=COLORS["panel"],
                                  anchor="e")
        self.pos_label.pack(side="right")

        # Canvas als Fortschrittsbalken
        bar_frame = tk.Frame(right, bg=COLORS["border"], height=20)
        bar_frame.pack(fill="x", pady=(0, 6))
        bar_frame.pack_propagate(False)

        self.pos_canvas = tk.Canvas(bar_frame,
                                    height=20,
                                    bg=COLORS["bg"],
                                    highlightthickness=0,
                                    bd=0)
        self.pos_canvas.pack(fill="both", expand=True)
        self.pos_canvas.bind("<Configure>", self._redraw_bar)

        # Balken-Rechtecke auf Canvas
        self._bar_bg   = self.pos_canvas.create_rectangle(0, 0, 0, 20,
                                                           fill=COLORS["bg"],
                                                           outline="")
        self._bar_fill = self.pos_canvas.create_rectangle(0, 0, 0, 20,
                                                           fill=COLORS["ok"],
                                                           outline="")
        self._bar_target = self.pos_canvas.create_line(0, 0, 0, 20,
                                                        fill=accent,
                                                        width=2)
        self._bar_text = self.pos_canvas.create_text(4, 10,
                                                      anchor="w",
                                                      text="",
                                                      font=("Courier New", 7, "bold"),
                                                      fill=COLORS["bg"])

        # ── Zeile 3: Beschleunigung ──────────────
        accel_row = tk.Frame(right, bg=COLORS["panel"])
        accel_row.pack(fill="x", pady=(4, 0))

        tk.Label(accel_row, text="ACCEL  (stp/s²):",
                 font=("Courier New", 7, "bold"),
                 fg=COLORS["text_dim"], bg=COLORS["panel"]).pack(side="left")

        default_accel = 6000 if axis_id == 1 else 60000
        self._accel_var = tk.StringVar(value=str(default_accel))
        accel_entry = tk.Entry(accel_row,
                               textvariable=self._accel_var,
                               font=("Courier New", 9, "bold"),
                               fg=accent, bg=COLORS["bg"],
                               insertbackground=accent,
                               relief="flat", bd=4,
                               width=9,
                               justify="right")
        accel_entry.pack(side="left", padx=(6, 4))
        accel_entry.bind("<Return>", lambda e: self._send_accel())

        tk.Button(accel_row,
                  text="SET",
                  font=("Courier New", 7, "bold"),
                  fg=COLORS["bg"], bg=accent,
                  activebackground=COLORS["btn_hover"],
                  relief="flat", bd=0,
                  padx=6, pady=2,
                  cursor="hand2",
                  command=self._send_accel).pack(side="left")

        self.accel_status = tk.Label(accel_row, text="",
                                     font=("Courier New", 7),
                                     fg=COLORS["ok"], bg=COLORS["panel"])
        self.accel_status.pack(side="left", padx=4)

        # ── Zeile 4: Info + Stop ─────────────────
        info_row = tk.Frame(right, bg=COLORS["panel"])
        info_row.pack(fill="x", pady=(4, 0))

        tk.Label(info_row, text="SPD:",
                 font=("Courier New", 7),
                 fg=COLORS["text_dim"], bg=COLORS["panel"]).pack(side="left")
        self.speed_label = tk.Label(info_row, text="—",
                                    font=("Courier New", 7, "bold"),
                                    fg=COLORS["text_dim"], bg=COLORS["panel"])
        self.speed_label.pack(side="left", padx=(2, 8))

        tk.Label(info_row, text="RUN:",
                 font=("Courier New", 7),
                 fg=COLORS["text_dim"], bg=COLORS["panel"]).pack(side="left")
        self.running_label = tk.Label(info_row, text="—",
                                      font=("Courier New", 7, "bold"),
                                      fg=COLORS["text_dim"], bg=COLORS["panel"])
        self.running_label.pack(side="left", padx=(2, 0))

        tk.Button(info_row,
                  text="■ STOP",
                  font=("Courier New", 8, "bold"),
                  fg=COLORS["error"], bg=COLORS["btn_bg"],
                  activebackground=COLORS["btn_hover"],
                  activeforeground=COLORS["error"],
                  relief="flat", bd=0,
                  padx=8, pady=2,
                  cursor="hand2",
                  command=self._do_stop).pack(side="right")

        self._slider_after = None

    # ── Slider-Events ────────────────────────
    def _slider_press(self, event):
        self._dragging = True

    def _slider_release(self, event):
        self._dragging = False
        pos = int(self.slider_var.get())
        self._target_pos = pos
        self.target_label.config(text=f"{pos:,}")
        self._redraw_bar()
        self._send_move(pos)

    def _on_slider_move(self, val):
        """Während des Ziehens: nur Label + Markierung aktualisieren, noch nicht senden."""
        pos = int(float(val))
        self._target_pos = pos
        self.target_label.config(text=f"{pos:,}")
        self._redraw_bar()

    def _send_move(self, pos: int):
        if self.axis_id == 1:
            cmd = {"id": 1, "cmd": "move_to", "pos": pos, "speed": 300}
        else:
            cmd = {"id": 2, "cmd": "move_to", "pos": pos, "speed": 20000}
        self.send_cb(cmd)

    def _send_accel(self):
        try:
            val = int(self._accel_var.get())
            if val <= 0:
                raise ValueError
        except ValueError:
            self.accel_status.config(text="✘ ungültig", fg=COLORS["error"])
            return
        self.send_cb({"id": self.axis_id, "cmd": "set_accel", "accel": val})
        self.accel_status.config(text="✔ gesendet", fg=COLORS["ok"])
        self.after(1500, lambda: self.accel_status.config(text=""))

    # ── Fortschrittsbalken ───────────────────
    def _redraw_bar(self, event=None):
        w = self.pos_canvas.winfo_width()
        h = self.pos_canvas.winfo_height()
        if w < 2:
            return

        actual_x  = int(self._actual_pos  / self.max_pos * w)
        target_x  = int(self._target_pos  / self.max_pos * w)

        # Hintergrund
        self.pos_canvas.coords(self._bar_bg, 0, 0, w, h)

        # Grüner IST-Balken
        self.pos_canvas.coords(self._bar_fill, 0, 0, actual_x, h)

        # Farbige SOLL-Linie
        self.pos_canvas.coords(self._bar_target, target_x, 0, target_x, h)

        # Positions-Text im Balken
        text_x = min(actual_x - 4, w - 4) if actual_x > 30 else actual_x + 4
        anchor = "e" if actual_x > 30 else "w"
        self.pos_canvas.coords(self._bar_text, text_x, h // 2)
        self.pos_canvas.itemconfig(self._bar_text,
                                   text=f"{self._actual_pos:,}",
                                   anchor=anchor,
                                   fill=COLORS["bg"] if actual_x > 30 else COLORS["ok"])

    # ── Homing ──────────────────────────────
    def _do_home(self):
        self._set_homing(True)
        self.send_cb(HOME_CMD[self.axis_id])

    def _do_stop(self):
        self.send_cb({"id": self.axis_id, "cmd": "stop"})

    # ── Status-Update vom Controller ─────────
    def update_status(self, data: dict):
        pos     = data.get("pos")
        speed   = data.get("speed")
        running = data.get("running")
        homed   = data.get("homed")
        homing  = data.get("homing", False)

        if pos is not None:
            self._actual_pos = int(pos)
            self.pos_label.config(text=f"{int(pos):,}")
            self._redraw_bar()

        if speed is not None:
            self.speed_label.config(text=f"{int(speed):,} stp/s")

        if running is not None:
            color = COLORS["ok"] if running else COLORS["text_dim"]
            self.running_label.config(text="YES" if running else "NO", fg=color)
            self.status_dot.config(fg=COLORS["ok"] if running else COLORS["bg"])

        if homed is not None:
            if homed:
                self.homed_label.config(text="✔ HOMED", fg=COLORS["ok"])
                self._set_homing(False)
            else:
                self.homed_label.config(text="✘ NOT HOMED", fg=COLORS["warn"])

        if homing:
            self._set_homing(True)

    def _set_homing(self, active: bool):
        self._homing = active
        if active:
            self.home_btn.config(text="⏳\nHOMING", fg=COLORS["warn"])
            self.homed_label.config(text="HOMING…", fg=COLORS["warn"])
        else:
            self.home_btn.config(text="⌂\nHOME", fg=self.accent)


# ─────────────────────────────────────────────
#  Haupt-Applikation
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stepper UART Controller")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, False)
        self.minsize(720, 420)

        self.serial = SerialManager()
        self._build_ui()
        self._apply_ttk_style()

        self.after(200, self._show_port_dialog)
        self.after(100, self._poll_rx)
        self.after(200, self._poll_positions)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # Intervall für zyklisches Positions-Polling (ms)
    POLL_INTERVAL = 200

    # ── UI bauen ────────────────────────────
    def _build_ui(self):
        # ── Top-Bar ──
        topbar = tk.Frame(self, bg=COLORS["bg"], pady=0)
        topbar.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(topbar,
                 text="⚡ STEPPER CONTROLLER",
                 font=("Courier New", 15, "bold"),
                 fg=COLORS["accent1"], bg=COLORS["bg"],
                 anchor="w").pack(side="left")

        self.conn_label = tk.Label(topbar,
                                   text="● GETRENNT",
                                   font=("Courier New", 9, "bold"),
                                   fg=COLORS["error"], bg=COLORS["bg"],
                                   anchor="e")
        self.conn_label.pack(side="right")

        tk.Button(topbar, text="PORT WÄHLEN",
                  font=("Courier New", 8, "bold"),
                  fg=COLORS["bg"], bg=COLORS["accent1"],
                  activebackground="#00b8d9",
                  relief="flat", bd=0, padx=10, pady=4,
                  cursor="hand2",
                  command=self._show_port_dialog).pack(side="right", padx=(0, 10))

        # Separator
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=0)

        # ── Achsen-Panels ──
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=14)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        self.axis1 = AxisPanel(main,
                               axis_id=1,
                               label="ACHSE 1  — Motor ID 1",
                               max_pos=AXIS1_MAX,
                               accent=COLORS["accent1"],
                               send_cb=self._send)
        self.axis1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.axis2 = AxisPanel(main,
                               axis_id=2,
                               label="ACHSE 2  — Motor ID 2",
                               max_pos=AXIS2_MAX,
                               accent=COLORS["accent2"],
                               send_cb=self._send)
        self.axis2.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # ── Log-Box ──
        log_frame = tk.Frame(self, bg=COLORS["panel"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
        log_frame.pack(fill="x", padx=16, pady=(0, 12))

        log_hdr = tk.Frame(log_frame, bg=COLORS["border"])
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text=" SERIAL LOG",
                 font=("Courier New", 8, "bold"),
                 fg=COLORS["text_dim"], bg=COLORS["border"],
                 anchor="w").pack(side="left", pady=2, padx=6)
        tk.Button(log_hdr, text="CLR",
                  font=("Courier New", 7),
                  fg=COLORS["text_dim"], bg=COLORS["border"],
                  activebackground=COLORS["btn_bg"],
                  relief="flat", bd=0, padx=6, pady=2,
                  cursor="hand2",
                  command=self._clear_log).pack(side="right")

        self.log_text = tk.Text(log_frame,
                                height=5,
                                bg=COLORS["bg"],
                                fg=COLORS["text_dim"],
                                font=("Courier New", 8),
                                relief="flat",
                                bd=6,
                                state="disabled",
                                wrap="word")
        self.log_text.pack(fill="x")

        # Log-Tags
        self.log_text.tag_config("tx",    foreground="#60a5fa")
        self.log_text.tag_config("rx",    foreground=COLORS["text"])
        self.log_text.tag_config("ok",    foreground=COLORS["ok"])
        self.log_text.tag_config("error", foreground=COLORS["error"])
        self.log_text.tag_config("info",  foreground=COLORS["warn"])

    def _apply_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Horizontal.TScale",
                        background=COLORS["panel"],
                        troughcolor=COLORS["border"],
                        sliderrelief="flat",
                        sliderlength=18,
                        borderwidth=0)

    # ── Port-Dialog ─────────────────────────
    def _show_port_dialog(self):
        ports = self.serial.list_ports()
        dlg = PortDialog(self, ports)
        self.wait_window(dlg)
        if dlg.result:
            self._connect(dlg.result)

    def _connect(self, port: str):
        if self.serial.connected:
            self.serial.disconnect()
        ok = self.serial.connect(port)
        if ok:
            self.conn_label.config(
                text=f"● {port}  @{BAUDRATE}",
                fg=COLORS["ok"]
            )
            self._log(f"Verbunden: {port} @ {BAUDRATE} Baud", "info")
        else:
            self.conn_label.config(text="● FEHLER", fg=COLORS["error"])
            messagebox.showerror("Verbindungsfehler",
                                 f"Konnte {port} nicht öffnen.")

    # ── Serial senden ────────────────────────
    def _send(self, obj: dict):
        if not self.serial.connected:
            self._log("Nicht verbunden!", "error")
            return
        self.serial.send(obj)
        self._log("TX  " + json.dumps(obj), "tx")

    # ── RX-Polling ──────────────────────────
    def _poll_rx(self):
        try:
            while True:
                data = self.serial.rx_queue.get_nowait()
                self._handle_rx(data)
        except queue.Empty:
            pass
        self.after(50, self._poll_rx)

    # ── Zyklisches Positions-Polling ─────────
    def _poll_positions(self):
        if self.serial.connected:
            self.serial.send({"id": 1, "cmd": "get_pos"})
            self.serial.send({"id": 2, "cmd": "get_pos"})
        self.after(self.POLL_INTERVAL, self._poll_positions)

    def _handle_rx(self, data: dict):
        cmd = data.get("cmd", "")
        # get_pos-Antworten still verarbeiten (kein Log-Spam)
        if cmd == "get_pos":
            motor_id = data.get("id")
            if motor_id == 1:
                self.axis1.update_status(data)
            elif motor_id == 2:
                self.axis2.update_status(data)
            return

        tag = "ok" if data.get("status") == "ok" else "error"
        self._log("RX  " + json.dumps(data), tag)

        motor_id = data.get("id")
        if motor_id == 1:
            self.axis1.update_status(data)
        elif motor_id == 2:
            self.axis2.update_status(data)

    # ── Log ─────────────────────────────────
    def _log(self, msg: str, tag: str = "info"):
        self.log_text.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ── Cleanup ─────────────────────────────
    def _on_close(self):
        self.serial.disconnect()
        self.destroy()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import serial          # noqa
        import serial.tools.list_ports  # noqa
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip",
                               "install", "pyserial", "-q"])
        import serial
        import serial.tools.list_ports

    app = App()
    app.mainloop()