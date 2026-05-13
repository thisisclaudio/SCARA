from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class Step:
    type: str
    pos: tuple | int | None = None
    speed: int | None = None
    delay: int | None = None
    extra: dict = field(default_factory=dict)


def parse(path: str | Path) -> list[Step]:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    steps: list[Step] = []
    for raw in data.get("program", []):
        t = raw.pop("type")
        pos = raw.pop("pos", None)
        if isinstance(pos, list):
            pos = tuple(pos)
        steps.append(Step(
            type=t,
            pos=pos,
            speed=raw.pop("speed", None),
            delay=raw.pop("delay", None),
            extra=raw,
        ))
    return steps
