# SCARA Robot

Python control software for a SCARA robot arm. Programs are written in YAML and executed via a GUI or the command line.
 
[![Demo Video](https://img.youtube.com/vi/iSsy7wypNEk/maxresdefault.jpg)](https://www.youtube.com/watch?v=iSsy7wypNEk)
 
---
 
## Setup

```bash
git clone https://github.com/thisisclaudio/SCARA.git
cd SCARA
pip install -r requirements.txt
cp env.txt .env   # fill in your serial port
```

---

## Running

**With GUI (recommended)**
```bash
python application/mainG.py
```
The GUI lists all `.yaml` files in `application/`, lets you select one and run it.

**Headless (CLI)**
```bash
python application/main.py application/example_program.yaml
```

---

## Writing Programs

Programs live in `application/` as `.yaml` files. A program is a list of steps under the `program:` key.

```yaml
program:
  - type: moveJ
    pos: [250, 0, 100, 0]

  - type: gripper
    pos: open

  - type: wait
    delay: 500
```

The robot executes steps top to bottom. Add `#` comments anywhere.

---

## YAML Commands

### `moveJ` — Joint move
Moves to a position using joint-space interpolation (fastest, not a straight line in space).

```yaml
- type: moveJ
  pos: [x, y, z, rotation]
  speed: 1        # optional, 0.0–1.0
```

### `moveL` — Linear move
Moves in a straight line in Cartesian space.

```yaml
- type: moveL
  pos: [x, y, z, rotation]
  speed: 1        # optional
```

### `moveL1` — Linear move (no re-init)
Like `moveL` but faster for dense waypoints (e.g. drawing, circles). Use when chaining many small moves.

```yaml
- type: moveL1
  pos: [x, y, z, rotation_rad]  # rotation in radians here
```

### `gripper` — Gripper control

```yaml
- type: gripper
  pos: open       # fully open (40 mm)

- type: gripper
  pos: grip       # light grip (25 mm)

- type: gripper
  pos: closed     # fully closed (0 mm)

- type: gripper
  pos: 15         # any value 0–40 mm
```

### `wait` — Pause

```yaml
- type: wait
  delay: 1000     # milliseconds
```

---

## Coordinate System

`pos: [x, y, z, rotation]`

| Axis | Unit | Description |
|---|---|---|
| x | mm | forward/back from base |
| y | mm | left/right |
| z | mm | height |
| rotation | ° | end-effector rotation (except `moveL1` → radians) |

---

## How It Works

```
mainG.py  →  yaml_parser.py  →  oop/Robot.py
   │               │
   │        reads .yaml file
   │        returns list of Step objects
   │
   └─ loops through steps, calls robot.move_j() / move_l() / set_gripper() etc.
```

- **`mainG.py`** — entry point, initialises the robot once, starts the GUI
- **`yaml_parser.py`** — reads a `.yaml` file and returns a typed list of `Step` objects
- **`oop/Robot.py`** — hardware abstraction: kinematics, servo control, stepper

---

## Example: Pick & Place

```yaml
program:
  # home
  - type: moveJ
    pos: [200, 0, 100, 0]

  # move above object
  - type: moveJ
    pos: [140, 35, 100, 0]

  - type: gripper
    pos: open

  # descend
  - type: moveJ
    pos: [140, 35, 34, 0]
    speed: 0.5

  - type: gripper
    pos: closed

  # lift
  - type: moveJ
    pos: [140, 35, 100, 0]

  # place
  - type: moveJ
    pos: [26, 97, 100, 180]

  - type: moveJ
    pos: [26, 97, 38, 180]

  - type: gripper
    pos: open

  - type: moveJ
    pos: [26, 97, 100, 180]
```
