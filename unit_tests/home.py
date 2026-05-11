import serial
import json
import time

ser = serial.Serial("COM7", 115200, timeout=1)
time.sleep(2)
ser.reset_input_buffer()

# HOME command senden
cmd = {"id": 1, "cmd": "home", "speed": 6000, "accel": 60000}
# drive 
cmd = {"id":2,"cmd":"move_rel","steps":100,"speed":20000}

ser.write((json.dumps(cmd) + "\n").encode())

print("→ sent:", cmd)

# Antwort lesen bis homed
while True:
    line = ser.readline().decode(errors="ignore").strip()

    if not line or "{" not in line:
        continue

    try:
        data = json.loads(line[line.index("{"):])
        print("←", data)

        if data.get("homed"):
            print("HOME DONE")
            break

    except:
        pass

ser.close()