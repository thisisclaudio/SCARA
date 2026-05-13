"""YAML program parser for SCARA framework.
This module implements a starter parser for reading robot programs
from YAML files and converting them into structured step objects.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SUPPORTED_STEP_TYPES = {"moveJ", "moveL", "wait", "gripperSetPos"}


class YamlParserError(ValueError):
    pass


class YamlProgramParser:
    """Parser for SCARA robot program YAML files."""

    def __init__(self) -> None:
        self.program: List[Dict[str, Any]] = []

    def load(self, path: str) -> None:
        """Load a YAML program file into the parser."""
        if yaml is None:
            raise YamlParserError("PyYAML is required to parse YAML files. Install it with `pip install pyyaml`.")

        if not os.path.isfile(path):
            raise YamlParserError(f"YAML file not found: {path}")

        with open(path, "r", encoding="utf-8") as handle:
            content = yaml.safe_load(handle)

        if not isinstance(content, dict):
            raise YamlParserError("YAML program must be a mapping with a top-level 'program' key.")

        program = content.get("program")
        if program is None:
            raise YamlParserError("Missing top-level 'program' key in YAML file.")

        self.program = self._parse_program(program)

    def _parse_program(self, program: Any) -> List[Dict[str, Any]]:
        if not isinstance(program, list):
            raise YamlParserError("'program' value must be a list of steps.")

        parsed_steps: List[Dict[str, Any]] = []
        for index, step in enumerate(program, start=1):
            parsed_steps.append(self._parse_step(step, index))

        return parsed_steps

    def _parse_step(self, step: Any, index: int) -> Dict[str, Any]:
        if not isinstance(step, dict):
            raise YamlParserError(f"Step {index} must be a mapping.")

        step_type = step.get("type")
        if not isinstance(step_type, str):
            raise YamlParserError(f"Step {index}: missing or invalid 'type' field.")

        step_data = {"type": step_type}
        match step_type:
            case "moveJ" | "moveL":
                step_data["pos"] = self._parse_position(step, index)
                step_data["speed"] = self._parse_speed(step, index)
            case "wait":
                step_data["delay"] = self._parse_delay(step, index)
            case "gripperSetPos":
                step_data["pos"] = self._parse_gripper_position(step, index)
            case _:
                raise YamlParserError(
                    f"Step {index}: unknown step type '{step_type}'. Supported types: {', '.join(sorted(SUPPORTED_STEP_TYPES))}."
                )

        return step_data

    def _parse_position(self, step: Dict[str, Any], index: int) -> List[float]:
        pos = step.get("pos")
        if not isinstance(pos, list) or len(pos) != 3:
            raise YamlParserError(f"Step {index}: 'pos' must be a list of three numbers.")
        return [float(value) for value in pos]

    def _parse_speed(self, step: Dict[str, Any], index: int) -> int:
        speed = step.get("speed")
        if speed is None:
            raise YamlParserError(f"Step {index}: missing 'speed' for move command.")
        return int(speed)

    def _parse_delay(self, step: Dict[str, Any], index: int) -> int:
        delay = step.get("delay")
        if delay is None:
            raise YamlParserError(f"Step {index}: missing 'delay' for wait command.")
        return int(delay)

    def _parse_gripper_position(self, step: Dict[str, Any], index: int) -> int:
        pos = step.get("pos")
        if pos is None:
            raise YamlParserError(f"Step {index}: missing 'pos' for gripperSetPos command.")
        return int(pos)

    def get_program(self) -> List[Dict[str, Any]]:
        """Return the parsed program steps."""
        return self.program.copy()


def load_yaml_program(path: str) -> List[Dict[str, Any]]:
    """Convenience function for loading a YAML SCARA program."""
    parser = YamlProgramParser()
    parser.load(path)
    return parser.get_program()
