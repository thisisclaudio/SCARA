import argparse
import os
import sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from STservo_sdk import *  
MOTOR_MAP = {
    3: "achse",
    4: "greifer_rot",
    5: "greifer_open_close"
}

def connect():
    load_dotenv()
    port = os.getenv("COM_PORT_MOTOR")

    portHandler = PortHandler(port)
    packetHandler45 = scscl(portHandler)
    packetHandler3 = sts(portHandler)

    if not portHandler.openPort():
        raise RuntimeError("Port open failed")

    if not portHandler.setBaudRate(1000000):
        raise RuntimeError("Baudrate failed")

    return portHandler, packetHandler45, packetHandler3


def read(packetHandler, motor_id):
    pos, comm, err = packetHandler.ReadPos(motor_id)

    if comm != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(comm))
        return
    if err != 0:
        print(packetHandler.getRxPacketError(err))
        return

    print(f"Motor {motor_id} ({MOTOR_MAP.get(motor_id)}): {pos}")


def move(packetHandler, motor_id, pos):
    comm, err = packetHandler.WritePos(motor_id, pos, 0, 1000)

    if comm != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(comm))
    elif err != 0:
        print(packetHandler.getRxPacketError(err))
    else:
        print(f"Motor {motor_id} ({MOTOR_MAP.get(motor_id)}) → {pos}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    # read
    p_read = sub.add_parser("read")
    p_read.add_argument("id", type=int)

    # move
    p_move = sub.add_parser("move")
    p_move.add_argument("id", type=int)
    p_move.add_argument("pos", type=int)

    # helper commands
    sub.add_parser("list")

    args = parser.parse_args()

    if args.cmd == "list":
        for k, v in MOTOR_MAP.items():
            print(f"{k}: {v}")
        return

    portHandler, packetHandler45, packetHandler3 = connect()

    try:
        if args.cmd == "read":
            if args.id == 1:
                read(packetHandler3, args.id)
            else:
                read(packetHandler45, args.id)

        elif args.cmd == "move":
            if args.id == 1:
                move(packetHandler3, args.id, args.pos)
            else:
                move(packetHandler45, args.id, args.pos)

    finally:
        portHandler.closePort()


if __name__ == "__main__":
    main()