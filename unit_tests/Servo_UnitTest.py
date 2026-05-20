"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

OFFSET_SERVO3 = 340
OFFSET_SERVO4 = 10
OFFSET_SERVO5 = -241

import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

import os

import time
sys.path.insert(0, "..")   # adjust if needed

from oop.Servo import Servo_Motor
from STservo_sdk import * 
from dotenv import load_dotenv
load_dotenv()
COM_PORT_SERVO = os.getenv("COM_PORT_SERVO")
print(f"Using COM port for servo: {COM_PORT_SERVO}")

port_handler = PortHandler(COM_PORT_SERVO)

#servo3 = Servo_Motor(id=3, offset=OFFSET_SERVO3, model="st3215", port_handler=port_handler)
servo4 = Servo_Motor(id=4, offset=OFFSET_SERVO4, model="sc09", port_handler=port_handler)
#servo5 = Servo_Motor(id=5, offset=OFFSET_SERVO5, model="sc09", port_handler=port_handler)
#pos4 = servo4.get_position_raw()  # initialize position

if True:
    #servo4.set_position(0, speed=500) #802
    #servo4.set_position_ultra_raw(715-307, speed=800)
    time.sleep(3)
    servo4.set_position(0, speed=500) #802

while True:
    pos4 =servo4.get_position()
    print(f"Position: {pos4:.2f}")
    #pos4 =servo4.get_position_raw()
    #print(f"Position raw: {pos4:.2f}")
    time.sleep(0.1)

