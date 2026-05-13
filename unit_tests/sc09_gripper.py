"""
SC09 Gripper Framework
======================
Steuert einen Waveshare/Feetech SC09 Servo als Greifer.

SC09 Spezifikationen:
  - Protokoll  : SCS (scscl)
  - Position   : 0 – 1023  →  0° – 300°
  - Auflösung  : 1023 Schritte / 300° ≈ 0.293° pro Schritt
  - Kein Multiturn-Modus
  - Baudrate   : 1 000 000 bps (Standard)

Koordinatensystem (konfigurierbar via OPEN_POS / CLOSE_POS):
  - 0   = vollständig offen
  - 200 = vollständig geschlossen  (Standardwert – je nach Hardware anpassen)
"""

import sys
import os

# SDK-Pfad relativ zu diesem File eintragen (oder PYTHONPATH setzen)
SDK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SDK_PATH not in sys.path:
    sys.path.append(SDK_PATH)

from STservo_sdk import PortHandler, scscl, COMM_SUCCESS

# ── Konstanten ────────────────────────────────────────────────────────────────

BAUDRATE        = 1_000_000   # Standard-Baudrate SC09
RAW_MIN         = 0           # kleinste gültige Rohposition
RAW_MAX         = 1023        # größte gültige Rohposition
DEGREES_MAX     = 300.0       # mechanischer Verfahrbereich in Grad

DEFAULT_SPEED   = 500         # Standardgeschwindigkeit  (0 = max)
DEFAULT_TIME    = 0           # Zeitvorgabe 0 = Geschwindigkeit steuert

# Greifer-Positionen – an die eigene Hardware anpassen
OPEN_POS        = 0           # vollständig offen
CLOSE_POS       = 200         # vollständig geschlossen


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def degrees_to_raw(degrees: float) -> int:
    """Wandelt Grad (0 – 300) in Rohwert (0 – 1023) um."""
    raw = round(degrees / DEGREES_MAX * RAW_MAX)
    return max(RAW_MIN, min(RAW_MAX, raw))


def raw_to_degrees(raw: int) -> float:
    """Wandelt Rohwert (0 – 1023) in Grad (0 – 300) um."""
    return round(raw / RAW_MAX * DEGREES_MAX, 2)


# ── Gripper-Klasse ────────────────────────────────────────────────────────────

class SC09Gripper:
    """
    Steuerklasse für einen SC09-Servo als Greifer.

    Beispiel:
        gripper = SC09Gripper(servo_id=3, port="/dev/ttyUSB0")
        gripper.connect()
        gripper.open()
        gripper.close()
        gripper.set_angle(90.0)
        print(gripper.get_angle())
        gripper.disconnect()
    """

    def __init__(
        self,
        servo_id: int,
        port: str,
        baudrate: int = BAUDRATE,
        open_pos: int = OPEN_POS,
        close_pos: int = CLOSE_POS,
    ):
        """
        Parameters
        ----------
        servo_id  : Servo-ID (1 – 253)
        port      : serieller Port, z. B. '/dev/ttyUSB0' oder 'COM3'
        baudrate  : Baudrate (Standard: 1 000 000)
        open_pos  : Rohposition für „vollständig offen"
        close_pos : Rohposition für „vollständig geschlossen"
        """
        self.servo_id  = servo_id
        self.port      = port
        self.baudrate  = baudrate
        self.open_pos  = open_pos
        self.close_pos = close_pos

        self._port_handler   = None
        self._packet_handler = None
        self._connected      = False

    # ── Verbindung ────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Öffnet den seriellen Port und konfiguriert ihn."""
        self._port_handler = PortHandler(self.port)

        if not self._port_handler.openPort():
            raise IOError(f"Port konnte nicht geöffnet werden: {self.port}")
        print(f"[SC09] Port geöffnet: {self.port}")

        if not self._port_handler.setBaudRate(self.baudrate):
            self._port_handler.closePort()
            raise IOError(f"Baudrate konnte nicht gesetzt werden: {self.baudrate}")
        print(f"[SC09] Baudrate gesetzt: {self.baudrate}")

        self._packet_handler = scscl(self._port_handler)
        self._connected = True

    def disconnect(self) -> None:
        """Schließt die serielle Verbindung."""
        if self._port_handler is not None:
            self._port_handler.closePort()
            self._connected = False
            print("[SC09] Port geschlossen.")

    def _check_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("Gripper ist nicht verbunden. Zuerst connect() aufrufen.")

    # ── Diagnose ──────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Gibt True zurück, wenn der Servo antwortet."""
        self._check_connected()
        model, comm_result, error = self._packet_handler.ping(self.servo_id)
        if comm_result != COMM_SUCCESS:
            print(f"[SC09] Ping fehlgeschlagen: {self._packet_handler.getTxRxResult(comm_result)}")
            return False
        if error != 0:
            print(f"[SC09] Servo-Fehler: {self._packet_handler.getRxPacketError(error)}")
        print(f"[SC09] Ping OK – Modellnummer: {model}")
        return True

    # ── Lesen ─────────────────────────────────────────────────────────────────

    def get_position_raw(self) -> int | None:
        """Liest die aktuelle Position als Rohwert (0 – 1023)."""
        self._check_connected()
        pos, comm_result, error = self._packet_handler.ReadPos(self.servo_id)
        if comm_result != COMM_SUCCESS:
            print(f"[SC09] ReadPos fehlgeschlagen: {self._packet_handler.getTxRxResult(comm_result)}")
            return None
        if error != 0:
            print(f"[SC09] Servo-Fehler: {self._packet_handler.getRxPacketError(error)}")
        return pos

    def get_angle(self) -> float | None:
        """Liest die aktuelle Position in Grad (0.0 – 300.0)."""
        raw = self.get_position_raw()
        return raw_to_degrees(raw) if raw is not None else None

    def get_speed(self) -> int | None:
        """Liest die aktuelle Geschwindigkeit."""
        self._check_connected()
        speed, comm_result, error = self._packet_handler.ReadSpeed(self.servo_id)
        if comm_result != COMM_SUCCESS:
            print(f"[SC09] ReadSpeed fehlgeschlagen: {self._packet_handler.getTxRxResult(comm_result)}")
            return None
        return speed

    def is_moving(self) -> bool:
        """Gibt True zurück, solange der Servo in Bewegung ist."""
        self._check_connected()
        moving, comm_result, error = self._packet_handler.ReadMoving(self.servo_id)
        if comm_result != COMM_SUCCESS:
            return False
        return bool(moving)

    # ── Schreiben ─────────────────────────────────────────────────────────────

    def set_position_raw(self, raw: int, speed: int = DEFAULT_SPEED, time: int = DEFAULT_TIME) -> bool:
        """
        Fährt den Servo auf eine Rohposition (0 – 1023).

        Parameters
        ----------
        raw   : Zielposition (0 – 1023)
        speed : Geschwindigkeit (0 = max)
        time  : Zeitvorgabe in ms (0 = Geschwindigkeit steuert)
        """
        self._check_connected()
        raw = max(RAW_MIN, min(RAW_MAX, raw))

        comm_result, error = self._packet_handler.WritePos(
            self.servo_id, raw, time, speed
        )
        if comm_result != COMM_SUCCESS:
            print(f"[SC09] WritePos fehlgeschlagen: {self._packet_handler.getTxRxResult(comm_result)}")
            return False
        if error != 0:
            print(f"[SC09] Servo-Fehler: {self._packet_handler.getRxPacketError(error)}")
        return True

    def set_angle(self, degrees: float, speed: int = DEFAULT_SPEED) -> bool:
        """
        Fährt den Servo auf einen Winkel (0.0 – 300.0 Grad).

        Parameters
        ----------
        degrees : Zielwinkel in Grad
        speed   : Geschwindigkeit (0 = max)
        """
        raw = degrees_to_raw(degrees)
        print(f"[SC09] set_angle({degrees}°) → Rohwert {raw}")
        return self.set_position_raw(raw, speed)

    def set_openness(self, percent: float, speed: int = DEFAULT_SPEED) -> bool:
        """
        Fährt den Greifer auf einen prozentualen Öffnungsgrad.

        Parameters
        ----------
        percent : 0.0 = vollständig geschlossen, 100.0 = vollständig offen
        speed   : Geschwindigkeit (0 = max)
        """
        percent = max(0.0, min(100.0, percent))
        raw = round(self.open_pos + (self.close_pos - self.open_pos) * (1.0 - percent / 100.0))
        print(f"[SC09] set_openness({percent}%) → Rohwert {raw}")
        return self.set_position_raw(raw, speed)

    # ── Convenience-Methoden ──────────────────────────────────────────────────

    def open(self, speed: int = DEFAULT_SPEED) -> bool:
        """Öffnet den Greifer vollständig."""
        print("[SC09] Greifer öffnen …")
        return self.set_position_raw(self.open_pos, speed)

    def close(self, speed: int = DEFAULT_SPEED) -> bool:
        """Schließt den Greifer vollständig."""
        print("[SC09] Greifer schließen …")
        return self.set_position_raw(self.close_pos, speed)

    # ── Context-Manager-Unterstützung ─────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
