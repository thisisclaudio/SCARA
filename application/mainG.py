import sys
from pathlib import Path
import time
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from oop.Robot import Robot
from yaml_parser import parse


def run(program_file: str, robot: Robot, log_callback=None):
    """Führt ein YAML-Programm auf einem bestehenden Robot-Objekt aus."""
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    steps = parse(program_file)

    for step in steps:
        match step.type:
            case "moveJ":
                pos = np.array(step.pos, dtype=float)
                log(f"moveJ → {pos.tolist()}")
                pos[3] = pos[3] / 180 * np.pi
                robot.move_j(pos)
            case "moveL":
                pos = np.array(step.pos, dtype=float)
                log(f"moveL → {pos.tolist()}")
                pos[3] = pos[3] / 180 * np.pi
                robot.move_l(pos)
            case "moveL1":
                    pos = np.array(step.pos, dtype=float)
                    print(f"Moving to {pos} with moveL1")
                    #pos[3] = pos[3] / 180 * np.pi  # Convert degrees to radians
                    robot.move_l1(P2=pos[:4])
            case "gripper":
                log(f"gripper → {step.pos}")
                match step.pos:
                    case "open":
                        robot.set_gripper(distance=40)
                    case "grip":
                        robot.set_gripper(distance=25)
                    case "closed":
                        robot.set_gripper(distance=0)
                    case _:
                        if isinstance(step.pos, (int, float)) and 0 <= step.pos <= 40:
                            robot.set_gripper(distance=step.pos)
                        else:
                            log(f"Unbekannte Greifer-Position: {step.pos}")
            case "wait":
                log(f"wait → {step.delay} ms")
                time.sleep(step.delay / 1000)
            case _:
                log(f"Unbekannter Schritt-Typ: {step.type}")


if __name__ == "__main__":
    # Robot einmalig initialisieren, dann GUI starten
    robot = Robot()
    try:
        from gui import ScaraApp
        app = ScaraApp(robot=robot, run_fn=run)
        app.mainloop()
    except KeyboardInterrupt:
        print("Abgebrochen.")
        robot.shutdown()
