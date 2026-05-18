import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

from oop.Robot import Robot

if __name__ == "__main__":
    robot = Robot()
    print("Robot initialized successfully")
    robot.set_tcp_position([240, 0, 50, 0], speed_factor=1)
    while True:

        time.sleep(0.2)

