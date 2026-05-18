import os, sys, time
sys.path.insert(0, "..")
from Servo_Gripper import ServoGripper
from STservo_sdk import PortHandler
from dotenv import load_dotenv

load_dotenv()
COM_PORT_SERVO = "COM3"
port_handler = PortHandler(COM_PORT_SERVO
                           )

gripper = ServoGripper(
    id=5,
    port_handler=port_handler,
    open_raw_1=897,    # ← anpassen
    open_raw_2=800,    # ← anpassen
    close_raw_1=523,   # ← anpassen
    close_raw_2=794,   # ← anpassen
    offset=0,
    model="sc09",
)

SPEED = 300

print("=== ServoGripper Test ===")
input("Enter → open(1)");   gripper.open_fully(); time.sleep(1.5)

input("Enter → open(2)");   gripper.get_position(); time.sleep(1.5)
input("Enter → open(2)");   gripper.get_position_raw(); time.sleep(1.5)

input("Enter → open(2)");   gripper.close_for_dice(); time.sleep(1.5)

input("Enter → open(2)");   gripper.get_position(); time.sleep(1.5)
input("Enter → open(2)");   gripper.get_position_raw(); time.sleep(1.5)

input("Enter → close(1)");  gripper.close_fully(); time.sleep(1.5)

input("Enter → open(2)");   gripper.get_position(); time.sleep(1.5)
input("Enter → open(2)");   gripper.get_position_raw(); time.sleep(1.5)

input("Enter → close(2)");  gripper.close_for_dice(); time.sleep(1.5)

input("Enter → open(2)");   gripper.get_position(); time.sleep(1.5)
input("Enter → open(2)");   gripper.get_position_raw(); time.sleep(1.5)

input("Enter → open(3)");   gripper.open_fully(); time.sleep(1.5)
input("Enter → close(3)");  gripper.set_position(20); time.sleep(1.5)

input("Enter → open(2)");   gripper.get_position(); time.sleep(1.5)
input("Enter → open(2)");   gripper.get_position_raw(); time.sleep(1.5)


print("Fertig.")