"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

OFFSET_SERVO3 = -5230
OFFSET_SERVO4 = -518
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
servo3 = Servo_Motor(id=1, offset=OFFSET_SERVO3, port=COM_PORT_SERVO, model="st3215", port_handler=port_handler)
servo4 = Servo_Motor(id=4, offset=OFFSET_SERVO4, port=COM_PORT_SERVO, model="sc09", port_handler=port_handler)
servo5 = Servo_Motor(id=5, offset=OFFSET_SERVO5, port=COM_PORT_SERVO, model="sc09", port_handler=port_handler)

servo3.set_position_raw(10)

while True:
    pos3 = servo3.get_position_raw()
    print(f"Servo 3 position: {pos3:.2f}")
    time.sleep(0.2)




