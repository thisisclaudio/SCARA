#!/usr/bin/env python3
"""
Stepper UART Stream GUI
- COM Port Auswahl
- 2 Achsen
- Homing + Accel + Move
- ESP Stream (t:pos)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import json
import threading
import queue


BAUDRATE = 115200


# ─────────────────────────────────────────────
# Serial
# ─────────────────────────────────────────────
class SerialManager:
    def __init__(self):
        self.ser = None
        self.lock = threading.Lock()
        self.rx_queue = queue.Queue()
        self.running = False

    def connect(self, port):
        try:
            self.ser = serial.Serial(port, BAUDRATE, timeout=0.5)
            self.running = True
            threading.Thread(target=self._rx, daemon=True).start()
            return True
        except Exception as e:
            print(e)
            return False

    def disconnect(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self.ser = None

    def send(self, obj):
        if not self.ser:
            return
        payload = json.dumps(obj) + "\n"
        with self.lock:
            self.ser.write(payload.encode())

    def _rx(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    try:
                        self.rx_queue.put(json.loads(line))
                    except:
                        pass
            except:
                pass

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]

    @property
    def connected(self):
        return self.ser and self.ser.is_open


# ─────────────────────────────────────────────
# Port Dialog
# ─────────────────────────────────────────────
class PortDialog(tk.Toplevel):
    def __init__(self, parent, ports):
        super().__init__(parent)
        self.result = None
        self.title("COM Port")
        self.configure(bg="#0f1117")
        self.grab_set()

        tk.Label(self, text="Select Port",
                 fg="white", bg="#0f1117",
                 font=("Arial", 12, "bold")).pack(pady=10)

        self.var = tk.StringVar(value=ports[0] if ports else "")

        frame = tk.Frame(self, bg="#1a1d27")
        frame.pack(padx=10, pady=10)

        for p in ports:
            tk.Radiobutton(frame, text=p,
                           variable=self.var, value=p,
                           fg="white", bg="#1a1d27",
                           selectcolor="#0f1117").pack(anchor="w")

        tk.Button(self, text="Connect",
                  command=self.ok,
                  bg="#00d4ff").pack(pady=10)

    def ok(self):
        self.result = self.var.get()
        self.destroy()


# ─────────────────────────────────────────────
# Axis Panel (FULL)
# ─────────────────────────────────────────────
class AxisPanel(tk.Frame):
    def __init__(self, master, axis_id, max_pos, color, send_cb):
        super().__init__(master, bg="#1a1d27")

        self.axis_id = axis_id
        self.max_pos = max_pos
        self.send_cb = send_cb

        self.actual = 0

        tk.Label(self, text=f"Axis {axis_id}",
                 fg=color, bg="#1a1d27",
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=10)

        # Position
        self.pos_label = tk.Label(self, text="0", fg="white", bg="#1a1d27")
        self.pos_label.pack(anchor="w", padx=10)

        # Slider
        self.slider = ttk.Scale(self, from_=0, to=max_pos,
                                orient="horizontal")
        self.slider.pack(fill="x", padx=10)

        self.slider.bind("<ButtonRelease-1>", self.move)

        # Buttons row
        btns = tk.Frame(self, bg="#1a1d27")
        btns.pack(fill="x", padx=10, pady=5)

        tk.Button(btns, text="HOME",
                  command=self.home,
                  bg=color).pack(side="left")

        tk.Button(btns, text="STOP",
                  command=self.stop,
                  bg="#444").pack(side="left", padx=5)

        # Accel
        acc = tk.Frame(self, bg="#1a1d27")
        acc.pack(fill="x", padx=10, pady=5)

        tk.Label(acc, text="ACCEL",
                 fg="gray", bg="#1a1d27").pack(side="left")

        self.accel_var = tk.StringVar(value="600")
        tk.Entry(acc, textvariable=self.accel_var,
                 width=8).pack(side="left")

        tk.Button(acc, text="SET",
                  command=self.set_accel).pack(side="left", padx=5)

        # Bar
        self.canvas = tk.Canvas(self, height=18,
                                bg="#0f1117", highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=8)

        self.fill = self.canvas.create_rectangle(0, 0, 0, 18,
                                                  fill=color)
        
        self.move_accel = 30000 if axis_id == 2 else 600
        self.move_speed = 6000 if axis_id == 2 else 400

    # ───────────────
    def move(self, _):
        pos = int(self.slider.get())

        self.send_cb({
            "id": self.axis_id,
            "cmd": "move_to",
            "pos": pos,
            "speed": self.move_speed,
            "accel": self.move_accel
        })

    def home(self):
        if self.axis_id == 1:
            payload = {"id": 1, "cmd": "home", "speed": 300, "accel": 600}
        elif self.axis_id == 2:
            payload = {"id": 2, "cmd": "home", "speed": 6000, "accel": 30000}
        else:
            payload = {"id": self.axis_id, "cmd": "home"}

        self.send_cb(payload)

    def stop(self):
        self.send_cb({"id": self.axis_id, "cmd": "stop"})

    def set_accel(self):
        try:
            val = int(self.accel_var.get())
        except:
            return

        self.send_cb({
            "id": self.axis_id,
            "cmd": "set_accel",
            "accel": val
        })

    def update(self, pos):
        self.actual = int(pos)
        self.pos_label.config(text=str(self.actual))

        w = self.canvas.winfo_width()
        if w < 2:
            return

        x = int(self.actual / self.max_pos * w)
        self.canvas.coords(self.fill, 0, 0, x, 18)


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Stepper GUI FULL")
        self.geometry("850x480")
        self.configure(bg="#0f1117")

        self.serial = SerialManager()

        top = tk.Frame(self, bg="#0f1117")
        top.pack(fill="x")

        tk.Button(top, text="CONNECT",
                  command=self.connect).pack(side="left")

        self.status = tk.Label(top, text="DISCONNECTED",
                               fg="red", bg="#0f1117")
        self.status.pack(side="right")

        body = tk.Frame(self, bg="#0f1117")
        body.pack(fill="both", expand=True)

        self.axis1 = AxisPanel(body, 1, 2500, "#00d4ff", self.send)
        self.axis1.pack(side="left", fill="both", expand=True, padx=5)

        self.axis2 = AxisPanel(body, 2, 58000, "#ff6b35", self.send)
        self.axis2.pack(side="left", fill="both", expand=True, padx=5)

        self.after(20, self.rx)

    # ───────────────
    def connect(self):
        ports = self.serial.list_ports()

        dlg = PortDialog(self, ports)
        self.wait_window(dlg)

        if dlg.result and self.serial.connect(dlg.result):
            self.status.config(text=dlg.result, fg="green")

            self.serial.send({"cmd": "stream", "interval": 50})

    def send(self, obj):
        if self.serial.connected:
            self.serial.send(obj)

    def rx(self):
        try:
            while True:
                msg = self.serial.rx_queue.get_nowait()

                if msg.get("t") == "pos":
                    self.axis1.update(msg.get("p1", 0))
                    self.axis2.update(msg.get("p2", 0))
        except queue.Empty:
            pass

        self.after(20, self.rx)


if __name__ == "__main__":
    App().mainloop()