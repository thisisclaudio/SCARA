/*
 * Stepper UART Controller
 * Kommunikation via JSON über Serial (UART)
 * Protokoll: {"id":1,"cmd":"...","pos":...,"speed":...}\n
 * Response: {"id":1,"status":"ok","pos":...,"speed":...}\n
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
#include "esp_timer.h"

// ─── Pin Definitionen ────────────────────────────────────────────────
#define PIN_EnableMotor 23
#define PIN_Dir1        21
#define PIN_Step1       22
#define PIN_Dir2        25
#define PIN_Step2       33

// Home-Schalter Pins
#define PIN_HOME1 34
#define PIN_HOME2 35

// ─── Standardwerte Achse 1 ───────────────────────────────────────────
#define DEFAULT_MAX_SPEED_1  1000.0f
#define DEFAULT_ACCEL_1      2000.0f
#define HOMING_SPEED_1       300.0f
#define HOMING_ACCEL_1       600.0f

// ─── Standardwerte Achse 2 ───────────────────────────────────────────
#define DEFAULT_MAX_SPEED_2  18000.0f
#define DEFAULT_ACCEL_2      90000.0f
#define HOMING_SPEED_2       6000.0f
#define HOMING_ACCEL_2       90000.0f

#define HOME_SWITCH_ACTIVE LOW  // LOW wenn Schalter gedrückt

// ─── Stepper Objekte ─────────────────────────────────────────────────
AccelStepper stepper1(AccelStepper::DRIVER, PIN_Step1, PIN_Dir1);
AccelStepper stepper2(AccelStepper::DRIVER, PIN_Step2, PIN_Dir2);

// ─── Zustandsvariablen ───────────────────────────────────────────────
enum MotorMode { MODE_POSITION, MODE_VELOCITY };  // enum statt String → ISR-sicher

struct MotorState {
  bool      enabled;
  MotorMode mode;
  bool      homed;
  bool      homing;
  int       homingDir;  // Homing Richtung: -1 oder +1
};

MotorState state1 = {true, MODE_POSITION, false, false, -1};
MotorState state2 = {true, MODE_POSITION, false, false, -1};

// ─── Timer Handle ────────────────────────────────────────────────────
esp_timer_handle_t stepperTimer;

// ─── Hilfsfunktionen ─────────────────────────────────────────────────
AccelStepper& getMotor(int id)   { return (id == 1) ? stepper1 : stepper2; }
MotorState&   getState(int id)   { return (id == 1) ? state1  : state2;  }
int           getHomePin(int id) { return (id == 1) ? PIN_HOME1 : PIN_HOME2; }

float getDefaultMaxSpeed(int id) { return (id == 1) ? DEFAULT_MAX_SPEED_1 : DEFAULT_MAX_SPEED_2; }
float getDefaultAccel(int id)    { return (id == 1) ? DEFAULT_ACCEL_1     : DEFAULT_ACCEL_2;     }
float getHomingSpeed(int id)     { return (id == 1) ? HOMING_SPEED_1      : HOMING_SPEED_2;      }
float getHomingAccel(int id)     { return (id == 1) ? HOMING_ACCEL_1      : HOMING_ACCEL_2;      }

void sendOk(int id, const char* cmd, AccelStepper& motor) {
  StaticJsonDocument<256> resp;
  resp["id"]      = id;
  resp["status"]  = "ok";
  resp["cmd"]     = cmd;
  resp["pos"]     = (long)motor.currentPosition();
  resp["speed"]   = (long)motor.speed();
  resp["target"]  = (long)motor.targetPosition();
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

// ─── Homing-Loop Logik ───────────────────────────────────────────────
void IRAM_ATTR updateHoming(int id) {
  MotorState&   mstate  = getState(id);
  if (!mstate.homing) return;
  AccelStepper& motor   = getMotor(id);
  int           homePin = getHomePin(id);

  if (digitalRead(homePin) == HOME_SWITCH_ACTIVE) {
    motor.stop();
    motor.setCurrentPosition(0);
    mstate.homing = false;
    mstate.homed  = true;

    // Bestätigungsmeldung – aus ISR heraus nicht direkt Serial nutzen,
    // daher Flag setzen; wird im Loop gesendet
    // (siehe homingDoneFlag unten)
  }
}

// ─── Homing-Done Flags für Serial-Ausgabe im Loop ────────────────────
volatile bool homingDone1 = false;
volatile bool homingDone2 = false;

void IRAM_ATTR updateHomingISR(int id) {
  MotorState&   mstate  = getState(id);
  if (!mstate.homing) return;
  AccelStepper& motor   = getMotor(id);
  int           homePin = getHomePin(id);

  if (digitalRead(homePin) == HOME_SWITCH_ACTIVE) {
    motor.stop();
    motor.setCurrentPosition(0);
    mstate.homing = false;
    mstate.homed  = true;
    motor.setMaxSpeed(getDefaultMaxSpeed(id));
    motor.setAcceleration(getDefaultAccel(id));
    if (id == 1) homingDone1 = true;
    else         homingDone2 = true;
  }
}

// ─── Timer ISR: läuft alle 50µs = 20kHz ─────────────────────────────
void IRAM_ATTR onStepperTimer(void* arg) {
  updateHomingISR(1);
  updateHomingISR(2);

  if (state1.mode == MODE_VELOCITY) stepper1.runSpeed();
  else                              stepper1.run();

  if (state2.mode == MODE_VELOCITY) stepper2.runSpeed();
  else                              stepper2.run();
}

// ─── Befehlsverarbeitung ─────────────────────────────────────────────
void processCommand(const String& jsonStr) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, jsonStr);
  if (err) { sendError(0, "JSON parse error"); return; }

  int id = doc["id"] | 0;
  if (id < 1 || id > 2) { sendError(id, "Invalid motor id (1 or 2)"); return; }

  const char*   cmd    = doc["cmd"] | "";
  AccelStepper& motor  = getMotor(id);
  MotorState&   mstate = getState(id);

  // ── move_to ──────────────────────────────────────────────────────
  if (strcmp(cmd, "move_to") == 0) {
    if (!doc.containsKey("pos")) { sendError(id, "Missing 'pos'"); return; }
    long pos = doc["pos"].as<long>();
    if (doc.containsKey("speed")) motor.setMaxSpeed(doc["speed"].as<float>());
    mstate.mode = MODE_POSITION;
    motor.moveTo(pos);
    sendOk(id, cmd, motor);
  }
  // ── move_rel ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "move_rel") == 0) {
    if (!doc.containsKey("steps")) { sendError(id, "Missing 'steps'"); return; }
    long steps = doc["steps"].as<long>();
    if (doc.containsKey("speed")) motor.setMaxSpeed(doc["speed"].as<float>());
    mstate.mode = MODE_POSITION;
    motor.move(steps);
    sendOk(id, cmd, motor);
  }
  // ── set_speed ────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_speed") == 0) {
    if (!doc.containsKey("speed")) { sendError(id, "Missing 'speed'"); return; }
    float spd = doc["speed"].as<float>();
    motor.setMaxSpeed(spd);
    if (mstate.mode == MODE_VELOCITY) motor.setSpeed(spd);
    sendOk(id, cmd, motor);
  }
  // ── set_accel ────────────────────────────────────────────────────
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
    int   dir = doc["dir"]   | -1;
    float spd = doc["speed"] | getHomingSpeed(id);
    float acc = doc["accel"] | getHomingAccel(id);
    mstate.homing    = true;
    mstate.homed     = false;
    mstate.homingDir = dir;
    motor.setAcceleration(acc);
    motor.setMaxSpeed(spd);
    motor.move(dir * 1000000L);
    sendOk(id, cmd, motor);
  }
  // ── get_pos ──────────────────────────────────────────────────────
  else if (strcmp(cmd, "get_pos") == 0) {
    sendOk(id, cmd, motor);
  }
  // ── get_status ───────────────────────────────────────────────────
  else if (strcmp(cmd, "get_status") == 0) {
    StaticJsonDocument<300> resp;
    resp["id"]      = id;
    resp["status"]  = "ok";
    resp["cmd"]     = cmd;
    resp["pos"]     = (long)motor.currentPosition();
    resp["speed"]   = (long)motor.speed();
    resp["target"]  = (long)motor.targetPosition();
    resp["running"] = motor.isRunning();
    resp["mode"]    = (mstate.mode == MODE_VELOCITY) ? "velocity" : "position";
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
  // ── set_mode ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_mode") == 0) {
    const char* mode = doc["mode"] | "";
    if (strcmp(mode, "velocity") == 0) {
      mstate.mode = MODE_VELOCITY;
      float spd = doc["speed"] | 0.0f;
      motor.setSpeed(spd);
    } else if (strcmp(mode, "position") == 0) {
      mstate.mode = MODE_POSITION;
      motor.stop();
    } else {
      sendError(id, "Invalid mode. Use 'position' or 'velocity'");
      return;
    }
    sendOk(id, cmd, motor);
  }
  // ── set_zero ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "set_zero") == 0) {
    motor.setCurrentPosition(0);
    sendOk(id, cmd, motor);
  }
  else {
    sendError(id, "Unknown command");
  }
}

// ─── Setup ──────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  // Motor Enable
  pinMode(PIN_EnableMotor, OUTPUT);
  setMotorEnabled(true);

  // Home-Schalter
  pinMode(PIN_HOME1, INPUT);
  pinMode(PIN_HOME2, INPUT);

  // Stepper 1
  stepper1.setMaxSpeed(DEFAULT_MAX_SPEED_1);
  stepper1.setAcceleration(DEFAULT_ACCEL_1);

  // Stepper 2
  stepper2.setMaxSpeed(DEFAULT_MAX_SPEED_2);
  stepper2.setAcceleration(DEFAULT_ACCEL_2);

  // ─── Timer einrichten: 50µs Intervall = 20kHz ───────────────────
  esp_timer_create_args_t timerArgs = {
    .callback        = &onStepperTimer,
    .arg             = nullptr,
    .dispatch_method = ESP_TIMER_TASK,
    .name            = "stepper"
  };
  esp_timer_create(&timerArgs, &stepperTimer);
  esp_timer_start_periodic(stepperTimer, 50);  // 50 Mikrosekunden

  Serial.println("{\"status\":\"ready\",\"msg\":\"Stepper UART Controller bereit\"}");
}

// ─── Hauptschleife ──────────────────────────────────────────────────
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

  // Homing-Bestätigung senden (aus ISR als Flag gesetzt)
  if (homingDone1) {
    homingDone1 = false;
    StaticJsonDocument<128> resp;
    resp["id"]    = 1;
    resp["status"] = "ok";
    resp["cmd"]   = "home";
    resp["pos"]   = 0;
    resp["homed"] = true;
    serializeJson(resp, Serial);
    Serial.println();
  }
  if (homingDone2) {
    homingDone2 = false;
    StaticJsonDocument<128> resp;
    resp["id"]    = 2;
    resp["status"] = "ok";
    resp["cmd"]   = "home";
    resp["pos"]   = 0;
    resp["homed"] = true;
    serializeJson(resp, Serial);
    Serial.println();
  }
}
