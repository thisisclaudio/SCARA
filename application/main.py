import sys
from pathlib import Path
from time import time
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent / "oop"))

from oop.Robot import Robot

from yaml_parser import parse


def run(program_file: str):
    steps = parse(program_file)
    robot = Robot()

    try:
        for step in steps:
            match step.type:
                case "moveJ":
                    print(f"Moving to {step.pos} with moveJ")
                    step.pos[3] = step.pos[3] / 180 * np.pi  # Convert degrees to radians
                    robot.move_j(step.pos)
                case "moveL":
                    print(f"Moving to {step.pos} with moveL")
                    step.pos[3] = step.pos[3] / 180 * np.pi  # Convert degrees to radians
                    robot.move_l(step.pos)
                case "gripper":
                    print(f"Setting gripper position to {step.pos}")
                    match step.pos:
                        case "open":
                            robot.move_gripper(distance=40)
                        case "grip":
                            robot.move_gripper(distance=30)
                        case "closed":
                            robot.move_gripper(distance=0)
                        case _:
                            if isinstance(step.pos, (int, float)) and 0 <= step.pos <= 40:
                                robot.move_gripper(distance=step.pos)
                            else:
                                print(f"Unknown gripper position: {step.pos}")
                case "wait":
                    print(f"Waiting for {step.delay} ms")
                    time.sleep(step.delay / 1000)
                case _:
                    print(f"Unknown step type: {step.type}")
    finally:
        robot.shutdown()
        pass


if __name__ == "__main__":
    program = sys.argv[1] if len(sys.argv) > 1 else \
        str(Path(__file__).parent / "example_program.yaml")
    run(program)
