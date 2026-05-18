"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

OFFSET_SERVO3 = 323
OFFSET_SERVO4 = -2
OFFSET_SERVO5 = -241

import os
import sys
import time
sys.path.insert(0, "..")   # adjust if needed

from Servo import Servo_Motor
from STservo_sdk import * 
from dotenv import load_dotenv
load_dotenv()
COM_PORT_SERVO = os.getenv("COM_PORT_SERVO")
print(f"Using COM port for servo: {COM_PORT_SERVO}")

port_handler = PortHandler(COM_PORT_SERVO)
servo3 = Servo_Motor(id=3, offset=OFFSET_SERVO3, model="st3215", port_handler=port_handler)
servo4 = Servo_Motor(id=4, offset=OFFSET_SERVO4, model="sc09", port_handler=port_handler)
servo5 = Servo_Motor(id=5, offset=OFFSET_SERVO5, model="sc09", port_handler=port_handler)
pos4 = servo4.get_position_raw()  # initialize position

if True:
    servo4.set_position(1.5, speed=500) #802
    time.sleep(3)
    pos4 =servo4.get_position_raw()
    print(f"raw Pi/2: {pos4:.2f}")
    pos4 =servo4.get_position()
    print(f"Pi/2: {pos4:.2f}")
    

    servo4.set_position(-1.5, speed=500) #203
    time.sleep(3)
    pos4 =servo4.get_position_raw()
    print(f"raw -Pi/2: {pos4:.2f}")

    pos4 =servo4.get_position()
    print(f" -Pi/2: {pos4:.2f}")


    servo4.set_position(0, speed=500)
    time.sleep(3)
    pos4 =servo4.get_position()
    print(f"0: {pos4:.2f}")
    pos4 =servo4.get_position_raw()
    print(f"0: {pos4:.2f}")

while True:
    pos4 =servo4.get_position()
    print(f"Position: {pos4:.2f}")
    pos4 =servo4.get_position_raw()
    print(f"Position raw: {pos4:.2f}")
    time.sleep(1)

