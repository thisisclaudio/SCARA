"""
example_usage.py
~~~~~~~~~~~~~~~~
Zeigt wie StepperMotor analog zur Waveshare Motor-Klasse verwendet wird.
"""

from StepperDriver.StepperMotor import StepperController, StepperMotor
import time
import math

# ─── Controller verbinden ─────────────────────────────────────────────────────
ctrl = StepperController(port="COM5", baudrate=115200)

# ─── Motoren initialisieren ───────────────────────────────────────────────────
# steps_per_rev = 200 Schritte * 16 Microstepping = 3200
motor1 = StepperMotor(id=1, steps_per_rev=3200, controller=ctrl,
                      default_speed=12000, default_accel=6000)
motor2 = StepperMotor(id=2, steps_per_rev=3200, controller=ctrl,
                      default_speed=12000, default_accel=6000)

print(motor1)
print(motor2)

# ─── Homing ──────────────────────────────────────────────────────────────────
print("\n--- Homing ---")
motor1.home(direction=-1, blocking=True, timeout=30.0)
motor2.home(direction=-1, blocking=True, timeout=30.0)

# ─── Position lesen ───────────────────────────────────────────────────────────
print(f"\nMotor 1 Position: {motor1.get_position():.4f} rad")
print(f"Motor 2 Position: {motor2.get_position():.4f} rad")
print(f"Motor 1 Status:   {motor1.get_status()}")

# ─── Positionsmodus ───────────────────────────────────────────────────────────
print("\n--- Positionsmodus ---")
motor1.set_position(math.pi / 2)          # 90°
motor2.set_position(math.pi)              # 180°

motor1.wait_until_done(timeout=10.0)
motor2.wait_until_done(timeout=10.0)

print(f"Motor 1: {math.degrees(motor1.get_position()):.1f}°")
print(f"Motor 2: {math.degrees(motor2.get_position()):.1f}°")

# Mit expliziter Geschwindigkeit
motor1.set_position(0.0, speed=5000)
motor1.wait_until_done()

# ─── Relativbewegung ──────────────────────────────────────────────────────────
print("\n--- Relativbewegung ---")
motor1.move_relative(math.pi / 4)         # +45°
motor1.wait_until_done()
print(f"Motor 1 nach +45°: {math.degrees(motor1.get_position()):.1f}°")

# ─── Velocity-Modus ──────────────────────────────────────────────────────────
print("\n--- Velocity-Modus ---")
motor1.change_mode("velocity", speed=3000)
time.sleep(2.0)
motor1.set_speed(-3000)                   # Richtung umkehren
time.sleep(2.0)
motor1.stop()
motor1.change_mode("position")            # Zurück in Positionsmodus

# ─── Rohe Steps verwenden (analog set_position_raw / WritePosEx) ─────────────
print("\n--- Raw Steps ---")
motor1.set_position_raw(1600)             # Halbe Umdrehung in Steps
motor1.wait_until_done()
print(f"Raw pos: {motor1.get_position_raw()} steps")

# ─── Shutdown ─────────────────────────────────────────────────────────────────
motor1.shutdown()
motor2.shutdown()
ctrl.close()