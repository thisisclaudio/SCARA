"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

import sys
import time
sys.path.insert(0, "..")   # adjust if needed

from Stepper import StepperController


stepper = StepperController(offset1=0, offset2=0, com_port="COM7")
home_status = stepper.home(2, speed=6000)
print(f"Home status: {home_status}")
home_status = stepper.home(1, speed=400)
print(f"Home status: {home_status}")
pos2 = stepper.get_position(2)
print(f"Position of motor 2: {pos2:.2f} mm")
status = stepper.set_position(2, -100, speed=4000)
print(f"Set position status: {status}")
pos3 = stepper.get_position(2)
print(f"Position of motor 2 after move: {pos3:.2f} mm")

while True:
    time.sleep(1)