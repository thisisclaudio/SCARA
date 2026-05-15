"""
Manual test script for StepperController on COM7.
Run from the same folder as stepper_controller.py.
"""

import os
import sys
import time
sys.path.insert(0, "..")   # adjust if needed

from Servo import Servo_Motor
from STservo_sdk import * 
from dotenv import load_dotenv
load_dotenv()

port_handler = PortHandler(os.getenv("COM_PORT_MOTOR"))
packet_handler3 = sts(port_handler)
packet_handler45 = scscl(port_handler)

port_handler = PortHandler(os.getenv("COM_PORT_MOTOR"))
    
servo4 = Servo_Motor(id=4, offset=0, packet_handler=packet_handler45)
servo5 = Servo_Motor(id=5, offset=0, packet_handler=packet_handler45)

pos4 = servo4.get_position_raw()
print(f"Raw position of servo 4: {pos4}")
pos5 = servo5.get_position_raw()
print(f"Raw position of servo 5: {pos5}")

pos4 = servo4.get_position()
print(f"Position of servo 4: {pos4:.2f} rad")
pos5 = servo5.get_position()
print(f"Position of servo 5: {pos5:.2f} rad")





