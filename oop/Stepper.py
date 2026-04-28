import time
import math

class Stepper:
    def __init__(self, step_pin, dir_pin, enable_pin=None,
                 steps_per_rev=200, microstepping=16):

        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin

        self.steps_per_rev = steps_per_rev * microstepping
        self.position = 0  # steps

        # motion limits
        self.max_speed = 1500      # steps/s (realistisch in Python)
        self.acceleration = 3000   # steps/s^2

    # ---------------- GPIO ----------------

    def _write(self, pin, value):
        # hier GPIO implementieren (RPi.GPIO / gpiozero / etc.)
        pass

    def _pulse(self):
        self._write(self.step_pin, 1)
        time.sleep(2e-6)
        self._write(self.step_pin, 0)

    # ---------------- API like Servo ----------------

    def get_position_raw(self):
        return self.position

    def get_position(self):
        return self.position * 2 * math.pi / self.steps_per_rev

    def set_position(self, angle_rad, speed=None):
        target = int(angle_rad * self.steps_per_rev / (2 * math.pi))
        self.set_position_raw(target, speed)

    # ---------------- Core motion ----------------

    def set_position_raw(self, target, speed=None):
        delta = target - self.position
        if delta == 0:
            return

        direction = 1 if delta > 0 else 0
        self._write(self.dir_pin, direction)

        steps = abs(delta)

        vmax = self.max_speed if speed is None else min(speed, self.max_speed)
        acc = self.acceleration

        # Ramp calculation
        accel_steps = int((vmax * vmax) / (2 * acc))

        if accel_steps * 2 > steps:
            accel_steps = steps // 2  # triangle profile

        cruise_steps = steps - 2 * accel_steps

        # ---------- ACCEL ----------
        for i in range(accel_steps):
            v = math.sqrt(2 * acc * (i + 1))
            delay = 1.0 / v

            self._pulse()
            time.sleep(delay)

            self._update(direction)

        # ---------- CRUISE ----------
        delay = 1.0 / vmax
        for _ in range(cruise_steps):
            self._pulse()
            time.sleep(delay)

            self._update(direction)

        # ---------- DECEL ----------
        for i in range(accel_steps, 0, -1):
            v = math.sqrt(2 * acc * i)
            delay = 1.0 / v

            self._pulse()
            time.sleep(delay)

            self._update(direction)

    def _update(self, direction):
        if direction:
            self.position += 1
        else:
            self.position -= 1

    # ---------------- Velocity mode ----------------

    def set_speed(self, speed):
        direction = 1 if speed >= 0 else 0
        self._write(self.dir_pin, direction)

        delay = 1.0 / abs(speed)

        try:
            while True:
                self._pulse()
                time.sleep(delay)
                self._update(direction)
        except KeyboardInterrupt:
            pass

    def shutdown(self):
        if self.enable_pin is not None:
            self._write(self.enable_pin, 1)