import threading
import json
import time
import numpy as np
import serial


class StepperController:
    def __init__(self, offset1, offset2, com_port):
        self.offset1 = offset1
        self.offset2 = offset2
        self.com_port = com_port
        self.serial = SerialManager()
        self.serial.open_serial(com_port)
    

    def shutdown(self):
        self.serial.close_serial()
        print("StepperController shutdown")


    def get_position_raw(self, motor_id):
        self.serial.send({"id": motor_id, "cmd": "get_pos"})
        response = self.serial.get_latest_data()
        while response is None:
            time.sleep(0.01)
            response = self.serial.get_latest_data()
        return response["pos"] if "pos" in response else "blöd"


    def home(self, motor_id):
        self.serial.send({"id": motor_id, "cmd": "home"})
        status = self.serial.get_latest_data()
        while status is None:
            time.sleep(0.01)
            status = self.serial.get_latest_data()
        if status.get("homed"):
            return status
        status = self.serial.get_latest_data()
        while status is None:
            time.sleep(0.01)
            status = self.serial.get_latest_data()
        return status


    def get_position(self, motor_id):
        position_raw = self.get_position_raw(motor_id)
        if motor_id == 1:
            return (position_raw - self.offset1) * 2 * np.pi / 3200
        elif motor_id == 2:
            return (self.offset2 - position_raw) / 3200 * 8 
            # 8mm pro Umdrehung 
        return
    

    def get_speed(self, motor_id):
        return "get_speed not implemented yet"
        self.serial.send({"id": motor_id, "cmd": "get_speed"})
        speed = self.serial.get_latest_data()
        while speed is None:
            time.sleep(0.01)
            speed = self.serial.get_latest_data()
        return speed
    

    def set_position_raw(self, motor_id, position, speed=200):
        #debug msg
        #print(f"Setting motor {motor_id} to raw position {position} with speed {speed}")
        self.serial.send({"id": motor_id, "cmd": "move_to", "pos": position, "speed": speed})
        status = self.serial.get_latest_data()
        while status is None:
            time.sleep(0.01)
            status = self.serial.get_latest_data()
            
        return status


    def set_position(self, motor_id, position, speed=200):
        if motor_id == 1:
            position_raw = int(position * 3200 / (2 * np.pi) + self.offset1)
            speed = int(speed / (2 * np.pi) * 3200)  # Convert rad/s to raw speed
        elif motor_id == 2:
            position_raw = int(self.offset2 - position * 3200 / 8)
            speed = int(speed / 8 * 3200)  # Convert mm/s to raw speed

        status = self.set_position_raw(motor_id, position_raw, speed)
        return status


    def set_speed(self, speed, motor_id):
        self.serial.send({"id": motor_id, "cmd": "set_speed", "speed": speed})
        status = self.serial.get_latest_data()
        while status is None:
            time.sleep(0.01)
            status = self.serial.get_latest_data()
        return status


class SerialManager:
    def __init__(self):
        self.serial = None
        self.com_port = None
        self.serial_running = False
        self.latest_data = None
        self.lock = threading.Lock()


    def open_serial(self, com_port):
        if self.serial is None:
            try:
                self.serial = serial.Serial(com_port, 115200, timeout=1)
                #print(f"Serial port {com_port} opened successfully.")
                self.serial_running = True
                self.thread = threading.Thread(target=self._read_loop, daemon=True)
                self.thread.start()
            except serial.SerialException as e:
                print(f"Error opening serial port {com_port}: {e}")
                self.serial = None
        else:
            print("Serial port is already open.")


    def close_serial(self):
        if self.serial is not None:
            self.serial.close()
            #print("Serial port closed.")
            self.serial = None
            self.serial_running = False
        else:
            print("Serial port is not open.") 


    def send(self, data):
        if self.serial is not None and self.serial_running:
            payload = json.dumps(data) + "\n"
            with self.lock:
                self.serial.write(payload.encode())
        else:
            print("Serial port is not open or not running.")  


    def _read_loop(self):
        while self.serial_running:
            try:
                if self.serial is not None and self.serial.is_open and self.serial.in_waiting > 0:
                    line = self.serial.readline().decode(errors="ignore").strip()

                    if line:
                        try:
                            
                            self.latest_data = json.loads(line)
                        except json.JSONDecodeError:
                            pass
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                self.serial_running = False            
   
                    
    def get_latest_data(self):
        latest = self.latest_data
        self.latest_data = None
        return latest         