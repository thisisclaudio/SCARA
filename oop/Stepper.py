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
        self.mode = "position"

        # motion params
        self.max_speed = 2000      # steps/sec
        self.acceleration = 4000   # steps/sec^2

        # TODO: GPIO init hier rein
        # self._setup_gpio()

    # ---------------- GPIO ----------------

    def _write(self, pin, value):
        # hier dein GPIO rein (RPi.GPIO / pigpio)
        pass

    def _pulse(self):
        self._write(self.step_pin, 1)
        time.sleep(2e-6)   # 2 µs HIGH
        self._write(self.step_pin, 0)

    # ---------------- Basic ----------------

    def shutdown(self):
        if self.enable_pin is not None:
            self._write(self.enable_pin, 1)

    def get_position_raw(self):
        return self.position

    def get_position(self):
        return self.position * 2 * math.pi / self.steps_per_rev

    # ---------------- Motion ----------------

    def set_position(self, position, speed=None):
        target_steps = int(position * self.steps_per_rev / (2 * math.pi))
        self.set_position_raw(target_steps, speed)

    def set_position_raw(self, target, speed=None):
        if speed is None:
            speed = self.max_speed

        delta = target - self.position
        direction = 1 if delta >= 0 else 0

        self._write(self.dir_pin, direction)

        steps = abs(delta)
        if steps == 0:
            return

        # trapezoidal profile
        accel = self.acceleration
        vmax = min(speed, self.max_speed)

        # steps needed to reach vmax
        accel_steps = int((vmax ** 2) / (2 * accel))

        if accel_steps * 2 > steps:
            accel_steps = steps // 2  # triangular profile

        cruise_steps = steps - 2 * accel_steps

        step_count = 0
        current_speed = 0

        # --- ACCEL ---
        for i in range(accel_steps):
            current_speed = math.sqrt(2 * accel * (i + 1))
            delay = 1.0 / current_speed

            self._pulse()
            time.sleep(delay)

            self._update_position(direction)
            step_count += 1

        # --- CRUISE ---
        delay = 1.0 / vmax
        for i in range(cruise_steps):
            self._pulse()
            time.sleep(delay)

            self._update_position(direction)
            step_count += 1

        # --- DECEL ---
        for i in range(accel_steps, 0, -1):
            current_speed = math.sqrt(2 * accel * i)
            delay = 1.0 / current_speed

            self._pulse()
            time.sleep(delay)

            self._update_position(direction)
            step_count += 1

    def _update_position(self, direction):
        if direction == 1:
            self.position += 1
        else:
            self.position -= 1

    # ---------------- Velocity Mode ----------------

    def change_mode(self, mode):
        if mode not in ["position", "velocity"]:
            raise ValueError("Invalid mode")
        self.mode = mode

    def set_speed(self, speed):
        if self.mode != "velocity":
            raise ValueError("Not in velocity mode")

        direction = 1 if speed >= 0 else 0
        self._write(self.dir_pin, direction)

        speed = abs(speed)

        delay = 1.0 / speed

        try:
            while True:
                self._pulse()
                time.sleep(delay)
                self._update_position(direction)
        except KeyboardInterrupt:
            pass