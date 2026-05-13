homing cmd:

'''
{"id":1,"cmd":"home","speed":300,"accel":6000}
{"id":2,"cmd":"home","speed":6000,"accel":60000}
'''



{"id":1,"cmd":"move_rel","steps":1000000,"speed":20000}



{"id":1,"cmd":"move_to","pos":1000000,"speed":20000}


{"id":1,"cmd":"stop"}




Achse 2 Homing Parameer
"speed":6000,"accel":60000


Achse 1 Homing Parameter
"speed":12000,"accel":60000




Achse 2: 59000 Steps abe



Mach eine kleine demo applikation in python mit gui wo ich manuell 2 achsen fahren lassen kann.
dazzu soll es zwei hauptfelder geben im gui wo ich die achse je homen kann per button dazu soll wie folgt sien
{"id":1,"cmd":"home","speed":300,"accel":6000}
{"id":2,"cmd":"home","speed":6000,"accel":60000}

diesen befehl musst du einfahc per serial senden 

beim öffnen deer applikation soll ein popup kommen wo die verfügbaren com-ports angezeigt werden und dann soll man einen auswählen können um ihn zu verbinden... baudrate solll 115200 sein
- **Baudrate:** `115200`
- **Trennzeichen:** `\n` (Newline)
- **Format:** JSON (UTF-8)
  

Eben soll zwei Teilfelder pro achse 1 auf gui haben wo einerseits links je ein homing taster... daneben soll je ein slider sein für achse 1 von 0-2500 und für ahcse 2 von 0-58000 dafür soll für achse 1 wie folgt
{"id":2,"cmd":"move_to","pos":58000,"speed":20000}

udn für achse1 wie. folgt:
{"id":1,"cmd":"move_to","pos":2500,"speed":300}


es osll ienfach kleine demo app sein für die schrittmotor api doku:
# Stepper UART Controller – API Dokumentation

## Überblick

Der Stepper UART Controller steuert zwei Schrittmotoren über eine serielle JSON-Schnittstelle (UART). Befehle werden als JSON-Objekte über `Serial` gesendet und mit einem Zeilenumbruch (`\n`) abgeschlossen.

- **Baudrate:** `115200`
- **Trennzeichen:** `\n` (Newline)
- **Format:** JSON (UTF-8)

---

## Protokoll

### Request

```json
{"id": <1|2>, "cmd": "<befehl>", [optionale Parameter]}
```

| Feld  | Typ    | Pflicht | Beschreibung                         |
|-------|--------|---------|--------------------------------------|
| `id`  | int    | ✅      | Motor-ID: `1` oder `2`               |
| `cmd` | string | ✅      | Befehlsname (siehe unten)            |
| ...   | –      | –       | Befehlsspezifische Parameter         |

### Response (Erfolg)

```json
{"id": 1, "status": "ok", "cmd": "<befehl>", "pos": 0, "speed": 0, "target": 0, "running": false}
```

### Response (Fehler)

```json
{"id": 0, "status": "error", "msg": "<fehlermeldung>"}
```

---

## Standardwerte

| Parameter         | Wert       |
|-------------------|------------|
| Max. Geschwindigkeit | `120 000 steps/s` |
| Beschleunigung    | `60 000 steps/s²` |
| Homing-Geschwindigkeit | `5 000 steps/s` |
| Homing-Beschleunigung  | `3 000 steps/s²` |
| Home-Schalter aktiv    | `LOW`           |

---

## Befehle

### `move_to` – Absolute Positionierung

Fährt Motor zu einer absoluten Zielposition.

**Request:**
```json
{"id": 1, "cmd": "move_to", "pos": 5000}
{"id": 1, "cmd": "move_to", "pos": 5000, "speed": 80000}
```

| Parameter | Typ   | Pflicht | Beschreibung                          |
|-----------|-------|---------|---------------------------------------|
| `pos`     | long  | ✅      | Zielposition in Steps (absolut)       |
| `speed`   | float | ❌      | Maximale Geschwindigkeit in steps/s   |

---

### `move_rel` – Relative Positionierung

Fährt Motor um eine relative Schrittanzahl.

**Request:**
```json
{"id": 2, "cmd": "move_rel", "steps": -1000}
{"id": 2, "cmd": "move_rel", "steps": 500, "speed": 50000}
```

| Parameter | Typ   | Pflicht | Beschreibung                        |
|-----------|-------|---------|-------------------------------------|
| `steps`   | long  | ✅      | Schritte relativ zur aktuellen Pos. |
| `speed`   | float | ❌      | Maximale Geschwindigkeit in steps/s |

---

### `set_speed` – Geschwindigkeit setzen

Setzt die maximale Geschwindigkeit. Im `velocity`-Modus wird zusätzlich die aktuelle Fahrgeschwindigkeit gesetzt.

**Request:**
```json
{"id": 1, "cmd": "set_speed", "speed": 100000}
```

| Parameter | Typ   | Pflicht | Beschreibung                      |
|-----------|-------|---------|-----------------------------------|
| `speed`   | float | ✅      | Geschwindigkeit in steps/s        |

---

### `set_accel` – Beschleunigung setzen

**Request:**
```json
{"id": 1, "cmd": "set_accel", "accel": 40000}
```

| Parameter | Typ   | Pflicht | Beschreibung                       |
|-----------|-------|---------|-------------------------------------|
| `accel`   | float | ✅      | Beschleunigung in steps/s²          |

---

### `stop` – Sofortstopp

Stoppt den Motor mit der eingestellten Verzögerung (kein harter Stopp).

**Request:**
```json
{"id": 1, "cmd": "stop"}
```

---

### `home` – Homing-Sequenz

Fährt den Motor gegen den Home-Schalter und setzt die Position auf `0`. Nach erfolgreichem Homing wird eine zusätzliche Bestätigungsmeldung gesendet.

**Request:**
```json
{"id": 1, "cmd": "home"}
{"id": 1, "cmd": "home", "dir": -1, "speed": 5000, "accel": 3000}
```

| Parameter | Typ   | Pflicht | Beschreibung                                 |
|-----------|-------|---------|----------------------------------------------|
| `dir`     | int   | ❌      | Fahrtrichtung: `-1` (Standard) oder `+1`     |
| `speed`   | float | ❌      | Homing-Geschwindigkeit (Standard: `5000`)    |
| `accel`   | float | ❌      | Homing-Beschleunigung (Standard: `3000`)     |

**Homing-Abschluss Response:**
```json
{"id": 1, "status": "ok", "cmd": "home", "pos": 0, "homed": true}
```

> Nach dem Homing werden `max_speed` und `accel` auf die Standardwerte zurückgesetzt.

---

### `get_pos` – Position abfragen

**Request:**
```json
{"id": 1, "cmd": "get_pos"}
```

**Response:**
```json
{"id": 1, "status": "ok", "cmd": "get_pos", "pos": 1234, "speed": 0, "target": 1234, "running": false}
```

---

### `get_status` – Vollständigen Status abfragen

**Request:**
```json
{"id": 1, "cmd": "get_status"}
```

**Response:**
```json
{
  "id": 1,
  "status": "ok",
  "cmd": "get_status",
  "pos": 1234,
  "speed": 0,
  "target": 1234,
  "running": false,
  "mode": "position",
  "homed": true,
  "homing": false,
  "enabled": true
}
```

| Feld      | Typ    | Beschreibung                           |
|-----------|--------|----------------------------------------|
| `pos`     | long   | Aktuelle Position in Steps             |
| `speed`   | long   | Aktuelle Geschwindigkeit in steps/s    |
| `target`  | long   | Zielposition in Steps                  |
| `running` | bool   | `true` wenn Motor in Bewegung          |
| `mode`    | string | `"position"` oder `"velocity"`         |
| `homed`   | bool   | `true` wenn Homing erfolgreich         |
| `homing`  | bool   | `true` während aktiver Homing-Sequenz  |
| `enabled` | bool   | `true` wenn Motor aktiviert ist        |

---

### `enable` / `disable` – Motor aktivieren / deaktivieren

Steuert den Enable-Pin (`PIN_EnableMotor`). Beide Motoren teilen sich einen gemeinsamen Enable-Pin.

**Request:**
```json
{"id": 1, "cmd": "enable"}
{"id": 1, "cmd": "disable"}
```

> `disable` stoppt den Motor zusätzlich sofort.

---

### `set_mode` – Betriebsmodus wechseln

Wechselt zwischen Positionier- und Geschwindigkeitsmodus.

**Request:**
```json
{"id": 1, "cmd": "set_mode", "mode": "velocity", "speed": 30000}
{"id": 1, "cmd": "set_mode", "mode": "position"}
```

| Parameter | Typ    | Pflicht | Beschreibung                                     |
|-----------|--------|---------|--------------------------------------------------|
| `mode`    | string | ✅      | `"position"` oder `"velocity"`                   |
| `speed`   | float  | ❌      | Startgeschwindigkeit im `velocity`-Modus         |

> Im `velocity`-Modus wird `runSpeed()` verwendet (keine Beschleunigungsrampe, konstante Geschwindigkeit).  
> Im `position`-Modus wird `run()` verwendet (mit Beschleunigung/Verzögerung).

---

### `set_zero` – Aktuelle Position als Nullpunkt setzen

Setzt die aktuelle Motorposition intern auf `0`, ohne den Motor zu bewegen.

**Request:**
```json
{"id": 1, "cmd": "set_zero"}
```

---

## Hardware-Pinbelegung

| Signal        | Pin | Beschreibung                  |
|---------------|-----|-------------------------------|
| `EnableMotor` | 23  | Gemeinsamer Enable (LOW = an) |
| `Dir1`        | 21  | Richtung Motor 1              |
| `Step1`       | 22  | Takt Motor 1                  |
| `Dir2`        | 25  | Richtung Motor 2              |
| `Step2`       | 33  | Takt Motor 2                  |
| `HOME1`       | 34  | Home-Schalter Motor 1         |
| `HOME2`       | 35  | Home-Schalter Motor 2         |

---

## Startup-Meldung

Nach dem Boot sendet der Controller:

```json
{"status": "ready", "msg": "Stepper UART Controller bereit"}
```

---

## Fehler-Codes

| Fehlermeldung                        | Ursache                                      |
|--------------------------------------|----------------------------------------------|
| `JSON parse error`                   | Ungültiges JSON im Request                   |
| `Invalid motor id (1 or 2)`          | `id` ist nicht `1` oder `2`                  |
| `Missing 'pos'`                      | `pos`-Parameter fehlt bei `move_to`          |
| `Missing 'steps'`                    | `steps`-Parameter fehlt bei `move_rel`       |
| `Missing 'speed'`                    | `speed`-Parameter fehlt bei `set_speed`      |
| `Missing 'accel'`                    | `accel`-Parameter fehlt bei `set_accel`      |
| `Invalid mode. Use 'position' or 'velocity'` | Ungültiger Wert bei `set_mode`       |
| `Unknown command`                    | Unbekannter `cmd`-Wert                       |

---

## Beispiel-Session

```
→ {"id":1,"cmd":"home","dir":-1}
← {"id":1,"status":"ok","cmd":"home","pos":-500,"speed":-5000,"target":-1000000,"running":true}
← {"id":1,"status":"ok","cmd":"home","pos":0,"homed":true}

→ {"id":1,"cmd":"move_to","pos":10000,"speed":80000}
← {"id":1,"status":"ok","cmd":"move_to","pos":0,"speed":0,"target":10000,"running":true}

→ {"id":1,"cmd":"get_status"}
← {"id":1,"status":"ok","cmd":"get_status","pos":4231,"speed":80000,"target":10000,"running":true,"mode":"position","homed":true,"homing":false,"enabled":true}

→ {"id":1,"cmd":"stop"}
← {"id":1,"status":"ok","cmd":"stop","pos":7890,"speed":0,"target":7890,"running":false}
```




im slider soll ebenfalls die aktuelle position drinn stehen


 