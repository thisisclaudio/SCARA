import time
import math

class StepperMotor:
    def __init__(self, step_pin, dir_pin,
                 steps_per_rev=200, microstepping=16):

        self.step_pin = step_pin
        self.dir_pin = dir_pin

        self.steps_per_rev = steps_per_rev * microstepping
        self.position = 0  # steps

        self.max_speed = 1500      # steps/s (hardware-safe for Python)
        self.acceleration = 3000   # steps/s²

    # ---------------- GPIO ----------------

    def _write(self, pin, value):
        pass  # GPIO here

    def _pulse(self):
        self._write(self.step_pin, 1)
        time.sleep(2e-6)
        self._write(self.step_pin, 0)

    # ---------------- POSITION API (like servo) ----------------

    def get_position(self):
        return self.position * 2 * math.pi / self.steps_per_rev

    def set_position(self, target_rad, speed=1000):
        target = int(target_rad * self.steps_per_rev / (2 * math.pi))
        self._move_to(target, speed)

    # ---------------- CORE MOTION ----------------

    def _move_to(self, target, speed):
        delta = target - self.position
        if delta == 0:
            return

        direction = 1 if delta > 0 else 0
        self._write(self.dir_pin, direction)

        steps = abs(delta)

        vmax = min(speed, self.max_speed)
        acc = self.acceleration

        # ramp distance
        accel_steps = int((vmax * vmax) / (2 * acc))

        if accel_steps * 2 > steps:
            accel_steps = steps // 2  # triangular profile

        cruise_steps = steps - 2 * accel_steps

        # -------- ACCEL --------
        for i in range(accel_steps):
            v = math.sqrt(2 * acc * (i + 1))
            delay = 1.0 / v

            self._pulse()
            time.sleep(delay)
            self._update(direction)

        # -------- CRUISE --------
        delay = 1.0 / vmax
        for _ in range(cruise_steps):
            self._pulse()
            time.sleep(delay)
            self._update(direction)

        # -------- DECEL --------
        for i in range(accel_steps, 0, -1):
            v = math.sqrt(2 * acc * i)
            delay = 1.0 / v

            self._pulse()
            time.sleep(delay)
            self._update(direction)

    def _update(self, direction):
        self.position += 1 if direction else -1