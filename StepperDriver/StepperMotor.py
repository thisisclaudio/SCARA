"""
stepper_motor.py
~~~~~~~~~~~~~~~~
Stepper-Motor API über UART – analog zur Waveshare Motor-Klasse.

Abhängigkeiten:
    pip install pyserial

Beispiel:
    from stepper_motor import StepperController, StepperMotor

    ctrl = StepperController(port="/dev/ttyUSB0", baudrate=115200)
    motor1 = StepperMotor(id=1, steps_per_rev=3200, controller=ctrl)
    motor2 = StepperMotor(id=2, steps_per_rev=3200, controller=ctrl)

    motor1.home()
    motor1.set_position(1.5708)   # π/2 rad → 90°
    motor1.shutdown()
    ctrl.close()
"""

import json
import time
import threading
import serial
from typing import Optional


# ─── Kommunikations-Schicht ───────────────────────────────────────────────────

class StepperController:
    """
    Verwaltet die serielle Verbindung zum Arduino.
    Ein Controller kann mehrere Motoren bedienen (id=1, id=2).
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        self._lock = threading.Lock()
        self._ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(2.0)          # Arduino-Reset abwarten
        self._ser.reset_input_buffer()

    # ── Low-Level Send / Receive ──────────────────────────────────────────────

    def send(self, payload: dict) -> dict:
        """Sendet einen JSON-Befehl und gibt die JSON-Antwort zurück."""
        with self._lock:
            msg = json.dumps(payload) + "\n"
            self._ser.write(msg.encode())
            raw = self._ser.readline().decode().strip()
            if not raw:
                raise TimeoutError(f"Keine Antwort auf: {payload}")
            resp = json.loads(raw)
            if resp.get("status") == "error":
                raise RuntimeError(f"Motor-Fehler: {resp.get('msg')}")
            return resp

    def close(self):
        self._ser.close()

    # ── Befehls-Methoden (intern, werden von StepperMotor aufgerufen) ─────────

    def cmd_move_to(self, id: int, pos: int, speed: Optional[float] = None) -> dict:
        p = {"id": id, "cmd": "move_to", "pos": pos}
        if speed is not None:
            p["speed"] = speed
        return self.send(p)

    def cmd_move_rel(self, id: int, steps: int, speed: Optional[float] = None) -> dict:
        p = {"id": id, "cmd": "move_rel", "steps": steps}
        if speed is not None:
            p["speed"] = speed
        return self.send(p)

    def cmd_set_speed(self, id: int, speed: float) -> dict:
        return self.send({"id": id, "cmd": "set_speed", "speed": speed})

    def cmd_set_accel(self, id: int, accel: float) -> dict:
        return self.send({"id": id, "cmd": "set_accel", "accel": accel})

    def cmd_stop(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "stop"})

    def cmd_home(self, id: int, direction: int = -1) -> dict:
        return self.send({"id": id, "cmd": "home", "dir": direction})

    def cmd_get_pos(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "get_pos"})

    def cmd_get_status(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "get_status"})

    def cmd_enable(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "enable"})

    def cmd_disable(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "disable"})

    def cmd_set_mode(self, id: int, mode: str, speed: float = 0.0) -> dict:
        return self.send({"id": id, "cmd": "set_mode", "mode": mode, "speed": speed})

    def cmd_set_zero(self, id: int) -> dict:
        return self.send({"id": id, "cmd": "set_zero"})


# ─── Motor-Klasse (analog Waveshare) ─────────────────────────────────────────

class StepperMotor:
    """
    High-Level Stepper-Motor API – analog zur Waveshare Motor-Klasse.

    Positionen werden intern in Radiant angegeben (wie Waveshare),
    Steps-per-Rev bestimmt die Auflösung.

    Args:
        id            : Motor-ID (1 oder 2)
        steps_per_rev : Schritte pro Umdrehung (inkl. Microstepping)
                        z.B. 200 * 16 = 3200 bei 1/16-Stepping
        offset        : Offset in Radiant (wird auf get_position addiert)
        controller    : StepperController-Instanz
        default_speed : Standard-Geschwindigkeit in steps/s
        default_accel : Standard-Beschleunigung in steps/s²
    """

    TWO_PI = 6.283185307179586

    def __init__(
        self,
        id: int,
        steps_per_rev: int,
        controller: StepperController,
        offset: float = 0.0,
        default_speed: float = 12000.0,
        default_accel: float = 6000.0,
    ):
        self.id = id
        self.steps_per_rev = steps_per_rev
        self.offset = offset          # rad
        self.controller = controller
        self.mode = "position"

        # Standardwerte setzen
        self.controller.cmd_set_speed(self.id, default_speed)
        self.controller.cmd_set_accel(self.id, default_accel)
        self.controller.cmd_enable(self.id)

    # ── Einheiten-Konversion ──────────────────────────────────────────────────

    def _rad_to_steps(self, rad: float) -> int:
        """Radiant → Steps (analog: -position * 4096 / (2π) bei Waveshare)"""
        return int(rad * self.steps_per_rev / self.TWO_PI)

    def _steps_to_rad(self, steps: int) -> float:
        """Steps → Radiant"""
        return steps * self.TWO_PI / self.steps_per_rev

    # ── Lifecycle (analog Waveshare __init__ / shutdown) ──────────────────────

    def shutdown(self):
        """Motor stromlos schalten (kein Haltemoment)."""
        self.controller.cmd_disable(self.id)
        print(f"Motor {self.id} shutdown")

    # ── Position lesen ────────────────────────────────────────────────────────

    def get_position_raw(self) -> int:
        """Rohe Schrittposition vom Controller lesen."""
        resp = self.controller.cmd_get_pos(self.id)
        return resp["pos"]

    def get_position(self) -> float:
        """
        Aktuelle Position in Radiant (mit Offset).
        Analog: return -position_raw * 2π / 4096
        """
        raw = self.get_position_raw()
        return self._steps_to_rad(raw) + self.offset

    def get_speed(self) -> float:
        """Aktuelle Geschwindigkeit in steps/s."""
        resp = self.controller.cmd_get_pos(self.id)
        return resp.get("speed", 0)

    def get_status(self) -> dict:
        """Vollständigen Status als dict zurückgeben."""
        return self.controller.cmd_get_status(self.id)

    def is_running(self) -> bool:
        """True wenn der Motor noch in Bewegung ist."""
        resp = self.controller.cmd_get_pos(self.id)
        return bool(resp.get("running", False))

    # ── Position setzen ───────────────────────────────────────────────────────

    def set_position(self, position: float, speed: Optional[float] = None):
        """
        Fahre zu absoluter Position in Radiant.
        Analog: set_position(rad, speed)
        """
        if self.mode != "position":
            raise ValueError("Motor ist nicht im Positionsmodus. change_mode('position') aufrufen.")
        pos_rad = position - self.offset
        steps = self._rad_to_steps(pos_rad)
        self.set_position_raw(steps, speed)

    def set_position_raw(self, position: int, speed: Optional[float] = None):
        """
        Fahre zu absoluter Schrittposition.
        Analog: WritePosEx(id, position, speed, 0)
        """
        self.controller.cmd_move_to(self.id, position, speed)

    def move_relative(self, delta_rad: float, speed: Optional[float] = None):
        """Fahre um delta_rad Radiant relativ zur aktuellen Position."""
        steps = self._rad_to_steps(delta_rad)
        self.controller.cmd_move_rel(self.id, steps, speed)

    def move_relative_raw(self, steps: int, speed: Optional[float] = None):
        """Fahre um steps Schritte relativ."""
        self.controller.cmd_move_rel(self.id, steps, speed)

    # ── Geschwindigkeit ───────────────────────────────────────────────────────

    def set_speed(self, speed: float):
        """
        Setzt Geschwindigkeit (steps/s).
        Im Velocity-Modus: sofortige Wirkung.
        Im Position-Modus: wird als Maximalgeschwindigkeit gesetzt.
        Analog: WriteSpec(id, speed, 0)
        """
        if self.mode == "velocity":
            self.controller.cmd_set_mode(self.id, "velocity", speed)
        else:
            self.controller.cmd_set_speed(self.id, speed)

    def set_acceleration(self, accel: float):
        """Beschleunigung in steps/s² setzen."""
        self.controller.cmd_set_accel(self.id, accel)

    # ── Modus wechseln ────────────────────────────────────────────────────────

    def change_mode(self, mode: str, speed: float = 0.0):
        """
        Betriebsmodus wechseln: 'position' oder 'velocity'.
        Analog: ServoMode / WheelMode bei Waveshare.
        """
        if mode not in ("position", "velocity"):
            raise ValueError("Ungültiger Modus. Verwende 'position' oder 'velocity'.")
        self.controller.cmd_set_mode(self.id, mode, speed)
        self.mode = mode

    # ── Homing ────────────────────────────────────────────────────────────────

    def home(self, direction: int = -1, blocking: bool = True, timeout: float = 30.0):
        """
        Homing-Sequenz: fährt gegen Home-Schalter, setzt Position auf 0.

        Args:
            direction : -1 (negativ) oder +1 (positiv)
            blocking  : Wartet bis Homing abgeschlossen
            timeout   : Maximale Wartezeit in Sekunden
        """
        self.controller.cmd_home(self.id, direction)
        if blocking:
            deadline = time.time() + timeout
            while time.time() < deadline:
                status = self.get_status()
                if status.get("homed") and not status.get("homing"):
                    print(f"Motor {self.id}: Homing abgeschlossen (pos=0)")
                    return
                time.sleep(0.05)
            raise TimeoutError(f"Motor {self.id}: Homing Timeout nach {timeout}s")

    def set_zero(self):
        """Aktuelle Position als Nullpunkt setzen (kein Schalter nötig)."""
        self.controller.cmd_set_zero(self.id)

    # ── Stopp ─────────────────────────────────────────────────────────────────

    def stop(self):
        """Motor sofort anhalten."""
        self.controller.cmd_stop(self.id)

    # ── Warten ───────────────────────────────────────────────────────────────

    def wait_until_done(self, poll_interval: float = 0.02, timeout: float = 60.0):
        """Blockiert bis der Motor die Zielposition erreicht hat."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.is_running():
                return
            time.sleep(poll_interval)
        raise TimeoutError(f"Motor {self.id}: Timeout beim Warten auf Zielposition")

    def __repr__(self):
        return (
            f"StepperMotor(id={self.id}, "
            f"mode='{self.mode}', "
            f"steps_per_rev={self.steps_per_rev})"
        )