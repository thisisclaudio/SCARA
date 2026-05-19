import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

from oop.Robot import Robot

if __name__ == "__main__":
    robot = Robot()
    print("Robot initialized successfully")

    result  = robot.move_j([200, 50, 50, 0], speed_factor=1.0)
    result  = robot.move_j([200, 50, 100, 1.57], speed_factor=0.5)

    if not result:
        print()
        print("Failed to set TCP position. TCP position may be out of reach.")
        stop_requested = True

    try:
        while True:
            robot.move()
            robot.print_tcp_position()
            robot.print_motor_positions(raw=True)

    except KeyboardInterrupt:
        print("Abbruch durch Ctrl+C")
        robot.shutdown()
