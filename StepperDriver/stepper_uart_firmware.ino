/*
 * Stepper UART Controller
 * Kommunikation via JSON über Serial (UART)
 * Protokoll: {"id":1,"cmd":"...","pos":...,"speed":...}\n
 * Response:  {"id":1,"status":"ok","pos":...,"speed":...}\n
 *
 * Unterstützte Befehle:
 *   move_to    - Fahre zu absoluter Position (steps)
 *   move_rel   - Fahre relativ (steps)
 *   set_speed  - Setze Maximalgeschwindigkeit
 *   set_accel  - Setze Beschleunigung
 *   stop       - Sofortstopp
 *   home       - Homing-Sequenz (fährt gegen Home-Schalter)
 *   get_pos    - Position abfragen
 *   get_status - Status abfragen
 *   enable     - Motor aktivieren
 *   disable    - Motor deaktivieren
 *   set_mode   - Modus setzen: "position" oder "velocity"
 */

#include <AccelStepper.h>
#include <ArduinoJson.h>

// ─── Pin Definitionen ──────────────────────────────────────────────
#define PIN_EnableMotor  23
#define PIN_Dir1         21
#define PIN_Step1        22
#define PIN_Dir2         25
#define PIN_Step2        33

// Home-Schalter Pins
#define PIN_HOME1        34
#define PIN_HOME2        35

// ─── Standardwerte ─────────────────────────────────────────────────
#define DEFAULT_MAX_SPEED   120000.0f
#define DEFAULT_ACCEL        60000.0f
#define HOMING_SPEED          5000.0f
#define HOMING_ACCEL          3000.0f
#define HOME_SWITCH_ACTIVE    LOW       // LOW wenn Schalter gedrückt

// ─── Stepper Objekte ───────────────────────────────────────────────
AccelStepper stepper1(AccelStepper::DRIVER, PIN_Step1, PIN_Dir1);
AccelStepper stepper2(AccelStepper::DRIVER, PIN_Step2, PIN_Dir2);

// ─── Zustandsvariablen ─────────────────────────────────────────────
struct MotorState {
  bool enabled;
  String mode;       // "position" oder "velocity"
  bool homed;
  bool homing;
  int homingDir;     // Homing Richtung: -1 oder +1
};

MotorState state1 = {true, "position", false, false, -1};
MotorState state2 = {true, "position", false, false, -1};

// ─── Hilfsfunktionen ───────────────────────────────────────────────
AccelStepper& getMotor(int id) {
  return (id == 1) ? stepper1 : stepper2;
}

MotorState& getState(int id) {
  return (id == 1) ? state1 : state2;
}

int getHomePin(int id) {
  return (id == 1) ? PIN_HOME1 : PIN_HOME2;
}

void sendOk(int id, const char* cmd, AccelStepper& motor) {
  StaticJsonDocument<256> resp;
  resp["id"]     = id;
  resp["status"] = "ok";
  resp["cmd"]    = cmd;
  resp["pos"]    = (long)motor.currentPosition();
  resp["speed"]  = (long)motor.speed();
  resp["target"] = (long)motor.targetPosition();
  resp["running"] = motor.isRunning();
  serializeJson(resp, Serial);
  Serial.println();
}

void sendError(int id, const char* msg) {
  StaticJsonDocument<128> resp;
  resp["id"]     = id;
  resp["status"] = "error";
  resp["msg"]    = msg;
  serializeJson(resp, Serial);
  Serial.println();
}

void setMotorEnabled(bool en) {
  digitalWrite(PIN_EnableMotor, en ? LOW : HIGH);
}

// ─── Befehlsverarbeitung ───────────────────────────────────────────
void processCommand(const String& jsonStr) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, jsonStr);
  if (err) {
    sendError(0, "JSON parse error");
    return;
  }

  int id = doc["id"] | 0;
  if (id < 1 || id > 2) {
    sendError(id, "Invalid motor id (1 or 2)");
    return;
  }

  const char* cmd = doc["cmd"] | "";
  AccelStepper& motor = getMotor(id);
  MotorState&   mstate = getState(id);

  // ── move_to ──────────────────────────────────────────────────────
  if (strcmp(cmd, "move_to") == 0) {
    if (!doc.containsKey("pos")) { sendError(id, "Missing 'pos'"); return; }
    long pos = doc["pos"].as<long>();
    if (doc.containsKey("speed")) {
      motor.setMaxSpeed(doc["speed"].as<float>());
    }
    mstate.mode = "position";
    motor.moveTo(pos);
    sendOk(id, cmd, motor);
  }

  // ── move_rel ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "move_rel") == 0) {
    if (!doc.containsKey("steps")) { sendError(id, "Missing 'steps'"); return; }
    long steps = doc["steps"].as<long>();
    if (doc.containsKey("speed")) {
      motor.setMaxSpeed(doc["speed"].as<float>());
    }
    mstate.mode = "position";
    motor.move(steps);
    sendOk(id, cmd, motor);
  }

  // ── set_speed ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_speed") == 0) {
    if (!doc.containsKey("speed")) { sendError(id, "Missing 'speed'"); return; }
    float spd = doc["speed"].as<float>();
    motor.setMaxSpeed(spd);
    if (mstate.mode == "velocity") {
      motor.setSpeed(spd);
    }
    sendOk(id, cmd, motor);
  }

  // ── set_accel ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_accel") == 0) {
    if (!doc.containsKey("accel")) { sendError(id, "Missing 'accel'"); return; }
    motor.setAcceleration(doc["accel"].as<float>());
    sendOk(id, cmd, motor);
  }

  // ── stop ─────────────────────────────────────────────────────────
  else if (strcmp(cmd, "stop") == 0) {
    motor.stop();
    sendOk(id, cmd, motor);
  }

  // ── home ─────────────────────────────────────────────────────────
  else if (strcmp(cmd, "home") == 0) {
    int dir = doc["dir"] | -1;   // Standard: negative Richtung
    mstate.homing    = true;
    mstate.homed     = false;
    mstate.homingDir = dir;
    motor.setAcceleration(HOMING_ACCEL);
    motor.setMaxSpeed(HOMING_SPEED);
    motor.move(dir * 1000000L);  // grosse Strecke, wird beim Schalter gestoppt
    sendOk(id, cmd, motor);
  }

  // ── get_pos ───────────────────────────────────────────────────────
  else if (strcmp(cmd, "get_pos") == 0) {
    sendOk(id, cmd, motor);
  }

  // ── get_status ────────────────────────────────────────────────────
  else if (strcmp(cmd, "get_status") == 0) {
    StaticJsonDocument<300> resp;
    resp["id"]      = id;
    resp["status"]  = "ok";
    resp["cmd"]     = cmd;
    resp["pos"]     = (long)motor.currentPosition();
    resp["speed"]   = (long)motor.speed();
    resp["target"]  = (long)motor.targetPosition();
    resp["running"] = motor.isRunning();
    resp["mode"]    = mstate.mode;
    resp["homed"]   = mstate.homed;
    resp["homing"]  = mstate.homing;
    resp["enabled"] = mstate.enabled;
    serializeJson(resp, Serial);
    Serial.println();
  }

  // ── enable / disable ─────────────────────────────────────────────
  else if (strcmp(cmd, "enable") == 0) {
    mstate.enabled = true;
    setMotorEnabled(true);
    sendOk(id, cmd, motor);
  }
  else if (strcmp(cmd, "disable") == 0) {
    mstate.enabled = false;
    setMotorEnabled(false);
    motor.stop();
    sendOk(id, cmd, motor);
  }

  // ── set_mode ──────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_mode") == 0) {
    const char* mode = doc["mode"] | "";
    if (strcmp(mode, "velocity") == 0) {
      mstate.mode = "velocity";
      float spd = doc["speed"] | 0.0f;
      motor.setSpeed(spd);
    } else if (strcmp(mode, "position") == 0) {
      mstate.mode = "position";
      motor.stop();
    } else {
      sendError(id, "Invalid mode. Use 'position' or 'velocity'");
      return;
    }
    sendOk(id, cmd, motor);
  }

  // ── set_zero ──────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_zero") == 0) {
    motor.setCurrentPosition(0);
    sendOk(id, cmd, motor);
  }

  else {
    sendError(id, "Unknown command");
  }
}

// ─── Homing-Loop Logik ─────────────────────────────────────────────
void updateHoming(int id) {
  MotorState& mstate = getState(id);
  if (!mstate.homing) return;

  AccelStepper& motor = getMotor(id);
  int homePin = getHomePin(id);

  if (digitalRead(homePin) == HOME_SWITCH_ACTIVE) {
    motor.stop();
    motor.setCurrentPosition(0);
    mstate.homing = false;
    mstate.homed  = true;
    // Bestätigungsmeldung
    StaticJsonDocument<128> resp;
    resp["id"]     = id;
    resp["status"] = "ok";
    resp["cmd"]    = "home";
    resp["pos"]    = 0;
    resp["homed"]  = true;
    serializeJson(resp, Serial);
    Serial.println();
    // Beschleunigung zurücksetzen
    motor.setMaxSpeed(DEFAULT_MAX_SPEED);
    motor.setAcceleration(DEFAULT_ACCEL);
  }
}

// ─── Setup ────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  // Motor Enable
  pinMode(PIN_EnableMotor, OUTPUT);
  setMotorEnabled(true);

  // Home-Schalter (interner Pull-Up)
  pinMode(PIN_HOME1, INPUT);
  pinMode(PIN_HOME2, INPUT);

  // Stepper 1
  stepper1.setMaxSpeed(DEFAULT_MAX_SPEED);
  stepper1.setAcceleration(DEFAULT_ACCEL);

  // Stepper 2
  stepper2.setMaxSpeed(DEFAULT_MAX_SPEED);
  stepper2.setAcceleration(DEFAULT_ACCEL);

  Serial.println("{\"status\":\"ready\",\"msg\":\"Stepper UART Controller bereit\"}");
}

// ─── Hauptschleife ────────────────────────────────────────────────
String inputBuffer = "";

void loop() {
  // Seriellen Input lesen
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }

  // Homing prüfen
  updateHoming(1);
  updateHoming(2);

  // Motoren fahren
  if (state1.mode == "velocity") {
    stepper1.runSpeed();
  } else {
    stepper1.run();
  }

  if (state2.mode == "velocity") {
    stepper2.runSpeed();
  } else {
    stepper2.run();
  }
}
