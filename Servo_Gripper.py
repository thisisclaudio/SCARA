from Servo import Servo_Motor
from STservo_sdk import *
import time

 
DEFAULT_SPEED         = 300    # Standard-Fahrgeschwindigkeit
# ── ServoGripper-Klasse ───────────────────────────────────────────────────────
 
class ServoGripper(Servo_Motor):

    def __init__(
        self,
        id: int,
        port_handler,
        open_raw_1:  int = 897,
        open_raw_2: int = 800,
        close_raw_1: int = 523,
        close_raw_2: int = 794,
        offset:    int = 0,
        model:     str = "sc09",
    ):
        # ── 1. Eltern-Konstruktor aufrufen ────────────────────────────────────
        super().__init__(
            id=id,
            offset=offset,
            model=model,
            port_handler=port_handler,
        )
        # ── 2. Gripper-spezifische Attribute setzen ───────────────────────────
        self.open_raw_1  = open_raw_1
        self.open_raw_2  = open_raw_2
        self.close_raw_1 = close_raw_1
        self.close_raw_2 = close_raw_2
        self._contact_position: int | None = None   # zuletzt erkannte Greifposition


    def move_gripper(self, position_raw: int, speed: int = DEFAULT_SPEED) -> None:
        position_raw = self.check_position(position_raw)
        self.packet_handler.WritePos(self.id, int(position_raw), 0, int(speed))

    def open_fully(self, speed: int = DEFAULT_SPEED) -> None:
        self.move_gripper(self.open_raw_1, speed)
        
    def close_fully(self, speed: int = DEFAULT_SPEED) -> None:
        self.move_gripper(self.close_raw_1, speed)
        
    def close_for_dice(self, speed: int = DEFAULT_SPEED) -> None:
        self.move_gripper(self.close_raw_2, speed)
       
    def get_position_raw(self) -> int:
        position, comm_result, error = self.packet_handler.ReadPos(self.id)
        print(f"DEBUG: raw position from servo: {position}")
        return position  # ← Eltern-Methode
    
    def get_position(self) -> float:
        raw = self.get_position_raw()   # ← Eltern-Methode
        # Umrechnung von raw in mm (close is 523 open is 897)
        pos_mm = 40/(897-523) * (raw - 523)
        print(f"DEBUG: raw={raw}, pos_mm={pos_mm:.2f}")
        return pos_mm 
    def set_position(self, pos_mm: float, speed: int = DEFAULT_SPEED) -> None:
        # Umrechnung von mm in raw
        raw = int(pos_mm * (897-523)/40 + 523)
        self.move_gripper(raw, speed)
    def check_position(self,pos_raw: int, ) -> int:
        if pos_raw >= self.close_raw_1 and pos_raw <= self.open_raw_1:
            return pos_raw
        elif pos_raw < self.close_raw_1:
            return self.close_raw_1
            print(f"Warnung: Gripper-Position {pos_raw} unterhalb der Grenze. Korrigiert auf {self.close_raw_1}.")
        else:
            return self.open_raw_1
            print(f"Warnung: Gripper-Position {pos_raw} ausserhalb der Grenzen. Korrigiert auf {pos_capped}.")