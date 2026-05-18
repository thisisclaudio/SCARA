
from STservo_sdk import * 

class Servo_Motor:
    def __init__(self, id, offset, model, port_handler=None):
        self.id = id
        self.offset = offset
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

            position = position + self.offset - 512
            position = self.cap(position)
            return position 
        
        else:
            position, _, _, _ = self.packet_handler.ReadPosSpeed(self.id)
            #debug
            position = - position 
            position = position + self.offset + 2048
            position = self.cap(position)
            return position
        
    def cap(self,pos):
        if self.model == "sc09":
            if pos > 512:
                return pos - 1024
            if pos < -512:
                return pos + 1024
            return pos
        
        if pos > 2048:
            return pos - 4096
        if pos < -2048:
            return pos + 4096
        return pos
    
    
    
    def get_position(self):
        position_raw = self.get_position_raw()
        if self.model == "sc09":
            return position_raw * 2 * 3.141592653589793 *5 / 6 / 1024
        else:
            return position_raw * 2 * 3.141592653589793 / 4096


    def get_speed(self):
        _, speed, _, _ = self.packet_handler.ReadPosSpeed(self.id)
        return speed
    

    def set_position(self, position, speed=1000):
        if self.model == "sc09":
            position_raw = int(position * 1024 / (2 * 3.141592653589793) + 1024)
        else:
            position_raw = int(position / (2 * 3.141592653589793) * 4096)

        self.set_position_raw(position_raw, speed)
        return

    def set_position_raw(self, position, speed=100):
        if self.model == "sc09":
            position = position - self.offset - 512
            if position > 1024:
                position = position - 1024
            if position < 0:
                position = position + 1024
            self.packet_handler.WritePos(self.id, int(position), 0, int(speed))

        else: #st3215
            print(f"Pos before thing: {position}")
            position = position - self.offset - 2048
            position = - position 
            if position > 4096:
                position = position - 4096
            self.packet_handler.WritePosEx(self.id, int(position), int(speed), 0)
            
        


    def change_mode(self, mode):
        if self.model == "sc09":
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
        print("not implemented yet")
        return
        self.packet_handler.WriteSpec(self.id, int(speed), 0)
        return