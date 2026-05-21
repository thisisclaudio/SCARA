from re import match
from oop.Servo import Servo_Motor
from oop.Servo_Gripper import ServoGripper
from oop.Stepper import StepperController
import sys
import os
import numpy as np
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))  # oop/
parent_dir = os.path.abspath(os.path.join(current_dir, "..")) 
sys.path.append(parent_dir)
from STservo_sdk import *    

    
class Robot:
    # Constants for kinematics
    OFFSET_STEPPER_1 = 1425
    OFFSET_STEPPER_2 = 60000 - (5/8*3200)
    OFFSET_SERVO3 = 330
    OFFSET_SERVO4 = 10
    #OFFSET_SERVO5 = -241
    
    OFFSET_AXIS_01 = 155
    LENGTH_AXIS_23 = 125
    LENGTH_AXIS_34 = 125
    OFFSET_AXIS_34 = -30
    OFFSET_GRIPPER = -125
    
    MIN_RADIUS = 75
    MIN_Z = 10
    MAX_Z = 145
    MIN_THETA = 0
    MAX_THETA = np.pi

    SPEED_AXIS_1 = 1000/3200*2*np.pi        # rad/s
    SPEED_AXIS_2 = 18000/3200*8             # mm/s
    ACCELERATION_AXIS_2 = 90000        # rad/s^2
    SPEED_AXIS_3 = 1000/4096*2*np.pi        # rad/s
    SPEED_AXIS_4 = 300/(1024*5/6)*2*np.pi   # rad/s


    def __init__(self):
        load_dotenv()

        self.port_handler = PortHandler(os.getenv("COM_PORT_SERVO"))
        # open port
        if self.port_handler.openPort():
            print("Succeeded to open the port")
        else:
            print("Failed to open the port")
            quit()
        
        stepper_COM_port = os.getenv("COM_PORT_STEPPER")
        
        self.stepper_controller = StepperController(self.OFFSET_STEPPER_1, self.OFFSET_STEPPER_2, stepper_COM_port)
        self.motor_3 = Servo_Motor(3, self.OFFSET_SERVO3, "st3215", self.port_handler)
        self.motor_4 = Servo_Motor(4, self.OFFSET_SERVO4, "sc09", self.port_handler)
        self.motor_5 = ServoGripper(
                                    id=5,
                                    port_handler=self.port_handler,
                                    open_raw_1=897,
                                    open_raw_2=800,
                                    close_raw_1=523,
                                    close_raw_2=794,
                                    offset=0,
                                    model="sc09",
                                )

        self.path = []
        self.stepper_controller.home(2)
        self.stepper_controller.home(1)
        


    def shutdown(self):
        self.stepper_controller.shutdown()
        self.motor_3.shutdown()
        self.motor_4.shutdown()
        self.motor_5.shutdown()
        self.port_handler.closePort()
        print("Robot shutdown")
  
  
    def get_motor_positions(self, raw=False):
        if raw:
            pos1 = self.stepper_controller.get_position_raw(1)
            pos2 = self.stepper_controller.get_position_raw(2)
            pos3 = self.motor_3.get_position_raw()
            pos4 = self.motor_4.get_position_raw()
        else:
            pos1 = self.stepper_controller.get_position(1)
            pos2 = self.stepper_controller.get_position(2)
            pos3 = self.motor_3.get_position()
            pos4 = self.motor_4.get_position()
        return pos1, pos2, pos3, pos4


    def print_motor_positions(self, raw=False):
        pos1, pos2, pos3, pos4 = self.get_motor_positions(raw)
        #print(f"\rMotor_1: {pos1:<6} | Motor_2: {pos2:<6} | Motor_3: {pos3:<6} | Motor_4: {pos4:<6}")


    def get_tcp_position(self):
        theta1, l1, theta2, theta3 = self.get_motor_positions()

        #print(f"Motor positions: theta1={theta1}, l1={l1}, theta2={theta2}, theta3={theta3}")
        
        T54 = np.array([
            [1, 0, 0, self.LENGTH_AXIS_34],
            [0, 1, 0, 0],
            [0, 0, 1, self.OFFSET_GRIPPER],
            [0, 0, 0, 1]
        ])    
        T43 = np.array([
            [np.cos(theta2), -np.sin(theta2), 0, 0],
            [np.sin(theta2),  np.cos(theta2), 0, 0],
            [0, 0, 1, self.OFFSET_AXIS_34],
            [0, 0, 0, 1]
        ])
        # Translation zuu Gelenk von Achse 2
        T32 = np.array([
            [1, 0, 0, self.LENGTH_AXIS_23],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        # Translation auf Drehplatte Achse 1
        T21 = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, l1+self.OFFSET_AXIS_01],
            [0, 0, 0, 1]
        ])
        # Rotation Achse 1
        T10 = np.array([
            [np.cos(theta1), -np.sin(theta1), 0, 0],
            [np.sin(theta1),  np.cos(theta1), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        theta = theta1 + theta2 + theta3

        pos = np.array([0, 0, 0, 1])
        pos = T10 @ T21 @ T32 @ T43 @ T54 @ pos

        pos = np.append(pos[:3], theta)
        
        # Format: [x, y, z, theta]
        return pos
    
    
    def set_tcp_position(self, tcp_position, speed_factor=1):
        x, y, z, theta = tcp_position

        z = z - self.OFFSET_AXIS_01 - self.OFFSET_AXIS_34 - self.OFFSET_GRIPPER

        c = np.sqrt(x**2 + y**2)
        a = self.LENGTH_AXIS_23
        b = self.LENGTH_AXIS_34

        phi = np.arccos((a**2 + b**2 - c**2) / (2*a*b))
        theta2 = np.pi - phi

        beta = theta2/2
        alpha = np.arctan2(y, x)
        theta1 = alpha - beta

        theta3 = theta - theta1 - theta2

        soll_pos = [theta1, z, theta2, theta3]
        
        #print(f"Setting TCP position to: x={x}, y={y}, z={z}, theta={theta}")
        #print(f"Calculated joint angles: theta1={theta1}, z={z}, theta2={theta2}, theta3={theta3}")

        #for index, pos in enumerate(soll_pos):
        #    if not self.check_workspace(index, pos, elbow_right=True):
        #        return False
        
        self.move_sync(soll_pos, speed_factor=speed_factor)
        return True
    
    
    def check_workspace(self, tcp_position, elbow_right=True):
        x, y, z, theta = tcp_position
        r1 = self.LENGTH_AXIS_23
        r2 = self.LENGTH_AXIS_34
        r = r1 + r2
        
        # Check z limits
        if z < self.MIN_Z:
            return False
        elif z > self.MAX_Z:
            return False
        
        # Check theta limits
        if theta < self.MIN_THETA:
            return False
        elif theta > self.MAX_THETA:
            return False

        # Check x, y limits based on elbow configuration
        if elbow_right:
            if x ** 2 + (y + r1) ** 2 < r ** 2:
                return False
            if x ** 2 + (y - r1) ** 2 <= r ** 2:
                return True
            if x < 0:
                return False
            if x ** 2 + y ** 2 > self.MIN_RADIUS ** 2:
                return False
            if x ** 2 + y ** 2 <= r ** 2:
                return True
            return False
        else:
            """
            if (x + r1) ** 2 + y ** 2 <= r ** 2:
                return True
            if (x - r1) ** 2 + y ** 2 < r ** 2:
                return False
            if y < 0:
                return False
            if x ** 2 + y ** 2 <= (2 * r) ** 2:
                return True
            """
            return False
    
    
    def move_sync(self, soll_pos, speed_factor=1):
        theta1_ist, z_ist, theta2_ist, theta3_ist = self.get_motor_positions()
        theta1_soll, z_soll, theta2_soll, theta3_soll = soll_pos

        #for index, pos in enumerate(soll_pos):
            #if not self.check_workspace(index, pos, elbow_right=True):
            #    return False

       #print(f"Current positions: theta1={theta1_ist}, z={z_ist}, theta2={theta2_ist}, theta3={theta3_ist}")
       #print(f"Target positions: theta1={theta1_soll}, z={z_soll}, theta2={theta2_soll}, theta3={theta3_soll}")

        theta1_time = abs(theta1_soll - theta1_ist) / self.SPEED_AXIS_1
        
        z_time_accel = self.SPEED_AXIS_2 / self.ACCELERATION_AXIS_2 * 2  # Time to accelerate to max speed and decelerate back to zero
        z_distance_accel = 0.5 * self.ACCELERATION_AXIS_2 * (z_time_accel / 2)**2  # Distance covered during acceleration and deceleration
        z_time_vmax = abs(z_soll - z_ist - z_distance_accel) / self.SPEED_AXIS_2
        if z_time_vmax < 0:
            # If the distance is too short to reach max speed, calculate the time for a triangular profile
            z_time = 2 * np.sqrt(abs(z_soll - z_ist) / self.ACCELERATION_AXIS_2)
        else:
            z_time = z_time_accel + z_time_vmax

        theta2_time = abs(theta2_soll - theta2_ist) / self.SPEED_AXIS_3
        theta3_time = abs(theta3_soll - theta3_ist) / self.SPEED_AXIS_4

        max_time = max(theta1_time, z_time, theta2_time, theta3_time)

        #print(f"max_time: {max_time}, theta1_time: {theta1_time}, z_time: {z_time}, theta2_time: {theta2_time}, theta3_time: {theta3_time}")

        speed_theta1 = speed_factor * self.SPEED_AXIS_1 * (theta1_time / max_time)
        speed_z = speed_factor * self.SPEED_AXIS_2 * (z_time / max_time)
        speed_theta2 = speed_factor * self.SPEED_AXIS_3 * (theta2_time / max_time)
        speed_theta3 = speed_factor * self.SPEED_AXIS_4 * (theta3_time / max_time)

        #print(f"Calculated speeds: speed_theta1={speed_theta1}, speed_z={speed_z}, speed_theta2={speed_theta2}, speed_theta3={speed_theta3}")

        self.stepper_controller.set_position(1, theta1_soll, speed=speed_theta1)
        self.stepper_controller.set_position(2, z_soll, speed=speed_z)
        self.motor_3.set_position(theta2_soll, speed=speed_theta2)
        self.motor_4.set_position(theta3_soll, speed=speed_theta3)


    def print_tcp_position(self):
        p = self.get_tcp_position()
        x, y, z, theta = p
        #print(f"\rTCP position: x={x:<6} | y={y:<6} | z={z:<6} | theta={theta:<6}", end="", flush=True)

    
    def move_l(self, target_position, start_position=None, step_size=2, speed_factor=1.0):
        #for index, pos in enumerate(target_position):
        #    if not self.check_workspace(index, pos, elbow_right=True):
        #        return False

        if not start_position:
            if not self.path:
                start_position = self.get_tcp_position()
            else:
                start_position = self.path[-1]
                start_position = start_position[:-1]  # remove speed factor from start position


       #print(f"Starting linear move from {start_position} to {target_position} with step size {step_size} and speed factor {speed_factor}")
        distance = np.linalg.norm(np.array(target_position) - np.array(start_position))
        if distance < step_size:
                target = [target_position, speed_factor]
                self.path.append(target)
                return True
        else:
            step_count = distance / step_size
            direction = (np.array(target_position) - np.array(start_position)) / step_count
           #print(f"Calculated {step_count} steps for linear move, direction: {direction}")
            for i in range(1, int(np.floor(step_count)) + 1):
                intermediate_position = start_position + direction * i
               #print(f"i: {i}, intermediate_position: {intermediate_position} Start: {start_position}, Target: {target_position}")
                target = np.append(intermediate_position, speed_factor)
                #if not self.check_workspace(intermediate_position, elbow_right=True):
                #    return False
                self.path.append(target)
            target = np.append(intermediate_position, speed_factor)
            self.path.append(target)

        self.move()
        return True
        
        
    def move_j(self, target_position, speed_factor=1.0):
        #for index, pos in enumerate(target_position):
            #if not self.check_workspace(index, pos, elbow_right=True):
            #    return False

        target = [target_position[0], target_position[1], target_position[2], target_position[3], speed_factor]
        self.path.append(target)
        self.move()
        return True
    
    
    def move(self, tolerance=5):
        if self.path:
            target_position = self.path[0]
            speed_factor = target_position[-1]
            target_position = target_position[:-1]
           #print(f"Target Pos: {target_position}")

            current_position = self.get_tcp_position()
            distance = np.linalg.norm(np.array(target_position) - np.array(current_position))

            #debug msg
            #print(f"Current TCP position: {current_position}, Target TCP position: {target_position}, Distance: {distance}")
            theta3_diff = abs(target_position[3] - current_position[3])

            if (distance < tolerance and theta3_diff < np.deg2rad(30)):  # If within tolerance, pop the target and move to the next one
                self.set_tcp_position(target_position, speed_factor=speed_factor) #vllt falsch
                #print(f"Reached target position: {target_position}")
                self.path.pop(0)
                if not self.path:
                    print("No more targets in path")
                else:
                    self.move()
            else:
                self.set_tcp_position(target_position, speed_factor=speed_factor)
                print(f"Moving towards target position: {target_position}, current position: {current_position}")
                self.move() # Continue moving towards the target position


    def move_gripper(self, distance=0, tolerance=5):
        current_distance = self.motor_5.get_position()
        print (f"Current gripper distance: {current_distance}, Target distance: {distance}")
        if abs(current_distance - distance) < tolerance:
            return True
        else:
            self.move_gripper(distance)


    def set_gripper(self, distance=0):
        self.motor_5.set_position(distance)
        self.move_gripper(distance)