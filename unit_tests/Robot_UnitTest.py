import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

from oop.Robot import Robot

if __name__ == "__main__":
    robot = Robot()
    print("Robot initialized successfully")

    '''
    result  = robot.move_j([190, 0, 10, 0], speed_factor=1.0)
    result  = robot.move_j([190, 0, 10, 1.57], speed_factor=1.0)
    result  = robot.move_j([190, 40, 10, 0], speed_factor=1.0)
    result  = robot.move_j([190, 40, 10, 1.57], speed_factor=1.0)
    result  = robot.move_j([190, -40, 10, 0], speed_factor=1.0)
    result  = robot.move_j([190, -40, 10, 1.57], speed_factor=1.0)
    #result  = robot.move_j([190, 0, 10, 1.57], speed_factor=1.0)
    '''
    result  = robot.move_j([190, -40, 50, 0], speed_factor=1.0)
    result = robot.move_l([190, -40, 0, 0], speed_factor=0.1)
    #result  = robot.move_j([190, -40, 70, 0], speed_factor=1.0)

    if not result:
        print()
        print("Failed to set TCP position. TCP position may be out of reach.")
        stop_requested = True


    print("Done!")
    robot.shutdown()
