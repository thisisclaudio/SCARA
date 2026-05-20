import sys
from pathlib import Path

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
                    robot.move_j(step.pos)
                case "moveL":
                    print(f"Moving to {step.pos} with moveL")
                    robot.move_l(step.pos)
                case "gripperSetPos":
                    print(f"Setting gripper position to {step.pos}")
                    # TODO: gripper integration
                    pass
                case "wait":
                    print(f"Waiting for {step.delay} ms")
                    #time.sleep(step.delay / 1000)
                case _:
                    print(f"Unknown step type: {step.type}")
    finally:
        robot.shutdown()
        pass


if __name__ == "__main__":
    program = sys.argv[1] if len(sys.argv) > 1 else \
        str(Path(__file__).parent / "example_program.yaml")
    run(program)
