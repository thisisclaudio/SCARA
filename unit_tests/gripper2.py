"""
SC09 Greifer – Interaktive Terminal-Steuerung
=============================================
Starte mit:
    python sc09_control.py
    python sc09_control.py --port /dev/ttyUSB0 --id 3
"""

import os
import sys
import argparse
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from sc09_gripper import SC09Gripper, raw_to_degrees, degrees_to_raw, RAW_MAX

load_dotenv()

COM_PORT  = os.getenv("COM_PORT_MOTOR", "/dev/ttyUSB0")
SERVO_ID  = int(os.getenv("SC09_ID",    "5"))
OPEN_POS  = int(os.getenv("SC09_OPEN",  "0"))
CLOSE_POS = int(os.getenv("SC09_CLOSE", "200"))

HELP_TEXT = """
┌─────────────────────────────────────────────┐
│         SC09 Greifer – Steuerung            │
├──────────────┬──────────────────────────────┤
│ o            │ Öffnen                        │
│ c            │ Schliessen                    │
│ a <grad>     │ Winkel setzen  (0 – 300°)     │
│ r <0-1023>   │ Rohwert setzen                │
│ p <%>        │ Öffnungsgrad   (0 – 100%)     │
│ s <speed>    │ Geschwindigkeit ändern        │
│ pos          │ Aktuelle Position lesen       │
│ ping         │ Verbindung prüfen             │
│ h            │ Hilfe anzeigen                │
│ q            │ Beenden                       │
└──────────────┴──────────────────────────────┘
"""

def print_status(gripper: SC09Gripper) -> None:
    raw = gripper.get_position_raw()
    if raw is not None:
        print(f"  Position: {raw} raw  |  {raw_to_degrees(raw)}°")
    else:
        print("  Position: konnte nicht gelesen werden")


def run(gripper: SC09Gripper) -> None:
    speed = 500
    print(HELP_TEXT)
    print(f"  Geschwindigkeit: {speed}  |  Offen={gripper.open_pos}  Zu={gripper.close_pos}\n")

    while True:
        try:
            raw_input = input("sc09> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[SC09] Beendet.")
            break

        if not raw_input:
            continue

        parts = raw_input.split()
        cmd   = parts[0].lower()

        if cmd in ("q", "quit", "exit"):
            print("[SC09] Beendet.")
            break

        elif cmd in ("h", "help"):
            print(HELP_TEXT)

        elif cmd == "o":
            gripper.open(speed=speed)
            print_status(gripper)

        elif cmd == "c":
            gripper.close(speed=speed)
            print_status(gripper)

        elif cmd == "a":
            if len(parts) < 2:
                print("  Verwendung: a <grad>   Beispiel: a 150")
                continue
            try:
                deg = float(parts[1])
                gripper.set_angle(deg, speed=speed)
                print_status(gripper)
            except ValueError:
                print("  Ungültiger Wert – Grad muss eine Zahl sein.")

        elif cmd == "r":
            if len(parts) < 2:
                print(f"  Verwendung: r <0-{RAW_MAX}>   Beispiel: r 512")
                continue
            try:
                raw = int(parts[1])
                gripper.set_position_raw(raw, speed=speed)
                print_status(gripper)
            except ValueError:
                print("  Ungültiger Wert – Rohwert muss eine ganze Zahl sein.")

        elif cmd == "p":
            if len(parts) < 2:
                print("  Verwendung: p <%>   Beispiel: p 50")
                continue
            try:
                pct = float(parts[1])
                gripper.set_openness(pct, speed=speed)
                print_status(gripper)
            except ValueError:
                print("  Ungültiger Wert – Prozent muss eine Zahl sein.")

        elif cmd == "s":
            if len(parts) < 2:
                print(f"  Aktuelle Geschwindigkeit: {speed}")
                print("  Verwendung: s <1-1000>   Beispiel: s 200")
                continue
            try:
                speed = max(1, min(1000, int(parts[1])))
                print(f"  Geschwindigkeit gesetzt: {speed}")
            except ValueError:
                print("  Ungültiger Wert – Geschwindigkeit muss eine ganze Zahl sein.")

        elif cmd == "pos":
            print_status(gripper)

        elif cmd == "ping":
            gripper.ping()

        else:
            print(f"  Unbekannter Befehl: '{cmd}'  –  'h' für Hilfe")


def main() -> None:
    parser = argparse.ArgumentParser(description="SC09 Greifer – Interaktive Steuerung")
    parser.add_argument("--port",  default=COM_PORT,  help=f"Serieller Port (Standard: {COM_PORT})")
    parser.add_argument("--id",    default=SERVO_ID,  type=int, help=f"Servo-ID (Standard: {SERVO_ID})")
    parser.add_argument("--open",  default=OPEN_POS,  type=int, help=f"Rohposition offen (Standard: {OPEN_POS})")
    parser.add_argument("--close", default=CLOSE_POS, type=int, help=f"Rohposition geschlossen (Standard: {CLOSE_POS})")
    args = parser.parse_args()

    print(f"\n[SC09] Verbinde mit Port {args.port}, ID {args.id} …")

    with SC09Gripper(
        servo_id  = args.id,
        port      = args.port,
        open_pos  = args.open,
        close_pos = args.close,
    ) as gripper:
        run(gripper)


if __name__ == "__main__":
    main()