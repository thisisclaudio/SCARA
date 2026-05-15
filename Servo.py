class Servo_Motor:
    def __init__(self, id, offset, packet_handler):
        self.id = id
        self.offset = offset
        self.packet_handler = packet_handler
        self.mode = "position"

        self.packet_handler.ServoMode(self.id)
        self.packet_handler.change_hold(self.id, 0)
        self.packet_handler.set_max_angle(self.id, 0)
        self.packet_handler.set_min_angle(self.id, 0)
        self.packet_handler.set_multiturn(self.id)
  

    def shutdown(self):
        self.packet_handler.change_hold(self.id, 0)
        print(f"Motor {self.id} shutdown")

    def get_position_raw(self):
        position, _, _, _ = self.packet_handler.ReadPosSpeed(self.id)
        if self.id == 1: 
            return position - 4096 + self.offset 
        else:
            return position - 1024 + self.offset ## evtl anpassen siehe 0 pos
    
    def get_position(self):
        position_raw = self.get_position_raw()
        if self.id == 1:
            return -position_raw * 2 * 3.141592653589793 / 4096
        else:
            return position_raw * 2 * 3.141592653589793 / 1024

    def get_speed(self):
        _, speed, _, _ = self.packet_handler.ReadPosSpeed(self.id)
        return speed
    
    def set_position(self, position, speed=1000):
        if self.id == 1:
            position_raw = int(-position * 4096 / (2 * 3.141592653589793) + 4096 - self.offset)
        else:
            position_raw = int(position * 1024 / (2 * 3.141592653589793) + 1024 - self.offset)

        self.set_position_raw(position_raw, speed)

    def set_position_raw(self, position, speed=1000):
        if self.id == 1:
            if position < 0:
                position = -32768 - position
        else:
            if position < 0:
                position = -1024 - position
                print("ahahahhahahahaha nico seit chunt nie so wiit siiiike✊")
        self.packet_handler.WritePosEx(self.id, position, int(speed), 0)

    def change_mode(self, mode):
        if mode == "position":
            self.packet_handler.ServoMode(self.id)
        elif mode == "velocity":
            self.packet_handler.WheelMode(self.id)
        else:
            raise ValueError("Invalid mode. Use 'position' or 'velocity'.")
        self.mode = mode

    def set_speed(self, speed):
        if self.mode != "velocity":
            raise ValueError("Motor is not in velocity mode. Call change_mode('velocity') first.")
        self.packet_handler.WriteSpec(self.id, int(speed), 0)
        