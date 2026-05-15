
from STservo_sdk import * 

class Servo_Motor:
    def __init__(self, id, offset, port, model, port_handler=None):
        self.id = id
        self.offset = offset
        self.port = port
        self.model = model
        self.mode = "position"
        self.port_handler = port_handler
        self.packet_handler = None
        self.connect()


    def connect(self):
        if not self.port_handler.openPort():
            raise RuntimeError("Failed to open port")

        if not self.port_handler.setBaudRate(1_000_000):
            raise RuntimeError("Failed to set baudrate")

        # IMPORTANT: choose protocol here
        if self.model == "sc09":
            self.packet_handler = scscl(self.port_handler)
        else:
            self.packet_handler = sts(self.port_handler)


    def shutdown(self):
        self.packet_handler.change_hold(self.id, 0)
        print(f"Motor {self.id} shutdown")


    def get_position_raw(self):        
        if self.model == "sc09": 
            position, comm_result, error = self.packet_handler.ReadPos(self.id)
            return position + self.offset 
        else:
            position, _, _, _ = self.packet_handler.ReadPosSpeed(self.id)
            return position + self.offset ## evtl anpassen siehe 0 pos #- 1024 +
    
    def get_position(self):
        position_raw = self.get_position_raw()
        if self.model == "st3215":
            return -position_raw * 2 * 3.141592653589793 / 4096
        else:
            return position_raw * 0.29296875 * 3.141592653589793 / 180

    def get_speed(self):
        _, speed, _, _ = self.packet_handler.ReadPosSpeed(self.id)
        return speed
    
    def set_position(self, position, speed=1000):
        if self.model == "st3215":
            position_raw = int(-position * 4096 / (2 * 3.141592653589793))
        else:
            position_raw = int(position * 1024 / (2 * 3.141592653589793) + 1024 - self.offset)

        self.set_position_raw(position_raw, speed)
        return

    def set_position_raw(self, position, speed=1000):
        if self.model == "st3215":
            position = -position
            if position < 0:
                position = -32768 - position
        else:
            if position < 0:
                #position = -1024 - position
                print("ahahahhahahahaha nico seit chunt nie so wiit siiiike✊")
        setPosMot = position - self.offset
        #debug message
        print(f"Setting servo {self.id} to raw position {position} set position motor {setPosMot} with speed {speed}")
        self.packet_handler.WritePosEx(self.id, setPosMot, int(speed), 0)

    def change_mode(self, mode):
        if self.id == 4 or self.id == 5:
            print("Warning: Servo 4 and 5 only support position mode. Ignoring mode change.")
            return

        if mode == "position":
            self.packet_handler.ServoMode(self.id)
        elif mode == "velocity":
            self.packet_handler.WheelMode(self.id)
        else:
            raise ValueError("Invalid mode. Use 'position' or 'velocity'.")
        self.mode = mode
        return

    def set_speed(self, speed):
        if self.mode != "velocity":
            raise ValueError("Motor is not in velocity mode. Call change_mode('velocity') first.")
        self.packet_handler.WriteSpec(self.id, int(speed), 0)
        return