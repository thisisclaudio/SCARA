"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

from pathlib import Path
import sys
import time
sys.path.insert(0, "..")   # adjust if needed
sys.path.append(str(Path(__file__).resolve().parent.parent))
from oop.Stepper import StepperController

offset1 = 1400
offset2 = 60000

stepper = StepperController(offset1=offset1, offset2=offset2, com_port="COM7")

axis = 1
pos = -1.28
home_status = stepper.home(axis)
print(f"Home status: {home_status}")
time.sleep(1)

pos1 = stepper.get_position_raw(axis)
print(f"Position of motor {axis}: {pos1:.2f} raw")
pos1 = stepper.get_position(axis)
print(f"Position of motor {axis}: {pos1:.2f} mm")

time.sleep(1)
status = stepper.set_position(axis, pos, speed=400)
print(f"Set position status: {status}")


while True:
    pos3 = stepper.get_position(axis)
    print(f"Position of motor {axis} after move: {pos3:.2f} mm")
    time.sleep(0.5)

