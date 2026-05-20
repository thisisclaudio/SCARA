import sys
from pathlib import Path
import time
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from oop.Robot import Robot

from yaml_parser import parse


def run(program_file: str):
    steps = parse(program_file)
    #print(f"steps {steps} steps from {program_file}")
    robot = Robot()

    try:
        for step in steps:
            match step.type:
                case "moveJ":
                    pos = np.array(step.pos, dtype=float)
                    print(f"Moving to {pos} with moveJ")
                    pos[3] = pos[3] / 180 * np.pi  # Convert degrees to radians
                    robot.move_j(pos)
                case "moveL":
                    pos = np.array(step.pos, dtype=float)
                    print(f"Moving to {pos} with moveL")
                    pos[3] = pos[3] / 180 * np.pi  # Convert degrees to radians
                    robot.move_l(pos)
                case "gripper":
                    print(f"Setting gripper position to {step.pos}")
                    match step.pos:
                        case "open":
                            robot.set_gripper(distance=40)
                        case "grip":
                            robot.set_gripper(distance=30)
                        case "closed":
                            robot.set_gripper(distance=0)
                        case _:
                            if isinstance(step.pos, (int, float)) and 0 <= step.pos <= 40:
                                robot.set_gripper(distance=step.pos)
                            else:
                                print(f"Unknown gripper position: {step.pos}")
                case "wait":
                    print(f"Waiting for {step.delay} ms")
                    time.sleep(step.delay / 1000)
                case _:
                    print(f"Unknown step type: {step.type}")
    except KeyboardInterrupt:
        print("Program interrupted by user, shutting down...")
    finally:
        robot.shutdown()
        pass


if __name__ == "__main__":
    program = sys.argv[1] if len(sys.argv) > 1 else \
        str(Path(__file__).parent / "cad_program.yaml")
    run(program)
