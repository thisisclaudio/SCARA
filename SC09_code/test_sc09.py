"""
SC09 Greifer – Testskript
=========================
Dieses Skript testet den SC09-Servo Schritt für Schritt.
Starte es direkt aus dem Projektverzeichnis:

    python unit_tests/test_sc09.py

Konfiguration via .env (gleiche Datei wie Motor-Tests):
    COM_PORT_MOTOR=/dev/ttyUSB0   (Linux/macOS)
    COM_PORT_MOTOR=COM3           (Windows)

Optionale Umgebungsvariablen:
    SC09_ID=3        Servo-ID (Standard: 3)
    SC09_OPEN=0      Rohposition „offen" (Standard: 0)
    SC09_CLOSE=200   Rohposition „geschlossen" (Standard: 200)
"""

import os
import sys
import time
import argparse

# Pfade einrichten
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from dotenv import load_dotenv
from sc09_gripper import SC09Gripper, raw_to_degrees, degrees_to_raw

# ── Konfiguration laden ───────────────────────────────────────────────────────

load_dotenv()

COM_PORT  = os.getenv("COM_PORT_MOTOR", "/dev/ttyUSB0")
SERVO_ID  = int(os.getenv("SC09_ID",    "1"))
OPEN_POS  = int(os.getenv("SC09_OPEN",  "0"))
CLOSE_POS = int(os.getenv("SC09_CLOSE", "200"))

# ── Testroutinen ──────────────────────────────────────────────────────────────

def separator(title: str) -> None:
    print("\n" + "─" * 50)
    print(f"  {title}")
    print("─" * 50)


def test_ping(gripper: SC09Gripper) -> None:
    separator("TEST: Ping")
    ok = gripper.ping()
    print(f"  Ergebnis: {'✓ OK' if ok else '✗ FEHLER'}")


def test_read_position(gripper: SC09Gripper) -> None:
    separator("TEST: Position lesen")
    raw = gripper.get_position_raw()
    if raw is not None:
        print(f"  Rohwert : {raw}")
        print(f"  Winkel  : {raw_to_degrees(raw)}°")
    else:
        print("  ✗ Konnte Position nicht lesen")


def test_open_close(gripper: SC09Gripper, pause: float = 1.5) -> None:
    separator("TEST: Öffnen / Schließen")

    print("  → Öffnen …")
    gripper.open()
    time.sleep(pause)
    pos = gripper.get_angle()
    print(f"  Position nach Öffnen: {pos}°")

    print("  → Schließen …")
    gripper.close()
    time.sleep(pause)
    pos = gripper.get_angle()
    print(f"  Position nach Schließen: {pos}°")

    print("  → Zurück zu offen …")
    gripper.open()
    time.sleep(pause)


def test_set_angle(gripper: SC09Gripper, pause: float = 1.5) -> None:
    separator("TEST: Winkel setzen")

    angles = [0.0, 50.0, 100.0, 150.0, 200.0, 300.0, 0.0]
    for target in angles:
        print(f"  → Fahre auf {target}° …")
        gripper.set_angle(target)
        time.sleep(pause)
        actual = gripper.get_angle()
        print(f"  Ist-Position: {actual}°")


def test_openness(gripper: SC09Gripper, pause: float = 1.5) -> None:
    separator("TEST: Öffnungsgrad (0 – 100 %)")

    for pct in [0, 25, 50, 75, 100, 0]:
        print(f"  → Öffnungsgrad {pct}% …")
        gripper.set_openness(pct)
        time.sleep(pause)
        print(f"  Ist-Position: {gripper.get_angle()}°")


def test_speed(gripper: SC09Gripper, pause: float = 2.0) -> None:
    separator("TEST: Verschiedene Geschwindigkeiten")

    for speed, label in [(100, "langsam"), (500, "mittel"), (1000, "schnell")]:
        print(f"  → Geschwindigkeit {speed} ({label}) …")
        gripper.close(speed=speed)
        time.sleep(pause)
        gripper.open(speed=speed)
        time.sleep(pause)


def test_moving(gripper: SC09Gripper) -> None:
    separator("TEST: Bewegungserkennung")
    gripper.open(speed=200)
    time.sleep(0.2)
    print("  Servo in Bewegung:", gripper.is_moving())
    time.sleep(2.0)
    print("  Servo in Bewegung (nach Pause):", gripper.is_moving())


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SC09 Greifer Testskript",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--test",
        choices=["all", "ping", "pos", "open_close", "angle", "openness", "speed", "moving"],
        default="all",
        help=(
            "Welcher Test soll ausgeführt werden?\n"
            "  all        – alle Tests\n"
            "  ping       – Verbindungstest\n"
            "  pos        – aktuelle Position lesen\n"
            "  open_close – Öffnen und Schließen\n"
            "  angle      – Winkel anfahren\n"
            "  openness   – prozentualer Öffnungsgrad\n"
            "  speed      – Geschwindigkeitstest\n"
            "  moving     – Bewegungserkennung\n"
        ),
    )
    parser.add_argument("--id",    type=int, default=SERVO_ID,  help=f"Servo-ID (Standard: {SERVO_ID})")
    parser.add_argument("--port",  type=str, default=COM_PORT,  help=f"Serieller Port (Standard: {COM_PORT})")
    parser.add_argument("--open",  type=int, default=OPEN_POS,  help=f"Rohposition offen (Standard: {OPEN_POS})")
    parser.add_argument("--close", type=int, default=CLOSE_POS, help=f"Rohposition geschlossen (Standard: {CLOSE_POS})")
    parser.add_argument("--pause", type=float, default=1.5,     help="Pause zwischen Bewegungen in Sekunden")
    args = parser.parse_args()

    print(f"\n{'═'*50}")
    print(f"  SC09 Greifer Test")
    print(f"{'═'*50}")
    print(f"  Port    : {args.port}")
    print(f"  ID      : {args.id}")
    print(f"  Offen   : {args.open}  ({raw_to_degrees(args.open)}°)")
    print(f"  Zu      : {args.close} ({raw_to_degrees(args.close)}°)")
    print(f"{'═'*50}")

    with SC09Gripper(
        servo_id  = args.id,
        port      = args.port,
        open_pos  = args.open,
        close_pos = args.close,
    ) as gripper:

        t = args.test
        p = args.pause

        if t in ("all", "ping"):        test_ping(gripper)
        if t in ("all", "pos"):         test_read_position(gripper)
        if t in ("all", "open_close"):  test_open_close(gripper, p)
        if t in ("all", "angle"):       test_set_angle(gripper, p)
        if t in ("all", "openness"):    test_openness(gripper, p)
        if t in ("all", "speed"):       test_speed(gripper, p)
        if t in ("all", "moving"):      test_moving(gripper)

    print("\n[SC09] Alle Tests abgeschlossen.\n")


if __name__ == "__main__":
    main()
