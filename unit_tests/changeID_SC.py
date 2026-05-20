import argparse
from dotenv import load_dotenv
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))  # unit_test/
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) 
sys.path.append(parent_dir)
from STservo_sdk import *                 # Uses STServo SDK library


def check_ids(id1, id2):
    if all(1 <= i <= 20 for i in (id1, id2)):
        print("Both IDs are valid.")
        return True
    else:
        print("Invalid IDs: Both must be between 1 and 20 (inclusive).")
        return False

# Set up argument parsing


id_old = 1
id_new = 4

# Validate the IDs
if check_ids(id_old, id_new):
    print("Proceeding with the operation.")
else:
    print("Operation aborted.")
    quit()

load_dotenv()

com_port_motor = "/dev/cu.usbmodem5AE60571561"
portHandler = PortHandler(com_port_motor)
packetHandler = sts(portHandler)
    
# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    quit()

# Set port baudrate
if portHandler.setBaudRate(1000000):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    quit()

sts_comm_result, sts_error = packetHandler.changeID(id_old, id_new) 
if sts_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(sts_comm_result))
elif sts_error != 0:
    print("%s" % packetHandler.getRxPacketError(sts_error))
    print("Now STServo ID is %d" % id_new)

# Close port
portHandler.closePort()
