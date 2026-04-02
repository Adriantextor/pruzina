# Návrh REST API

## 1. Účel dokumentu

Tento dokument definuje návrh REST API pre projekt Simulátor kmitajúcej pružiny so závažím. Cieľom je:

- presne určiť endpointy,
- uzamknúť formát request/response JSON,
- oddeliť správu konfigurácií od správy simulácií.

---

## 2. API princípy

- REST API sa používa na správu konfigurácií a simulácií.
- WebSocket sa používa iba na priebežné streamovanie dát simulácie.
- Frontend je klient API a nesmie obchádzať validáciu backendu.
- Všetky odpovede musia byť vo formáte JSON.
- Chybové odpovede musia byť čitateľné a konzistentné.

---

## 3. Základné URL

```
REST API:   /api/spring/...
WebSocket:  /ws/{simulation_id}
```

Všetko beží na jednom porte `8000` — FastAPI natívny WebSocket, žiadny samostatný WebSocket server.

---

## 4. Identifikátory

| Typ | Formát | Príklad |
|---|---|---|
| Configuration ID | string | `conf_abc123` |
| Simulation ID | string | `sim_xyz789` |

---

## 5. Povolené rozsahy parametrov

| Parameter | Typ | Rozsah | Predvolená hodnota |
|---|---|---|---|
| mass | float | > 0 kg | 1.0 |
| stiffness | float | > 0 N/m | 10.0 |
| damping | float | ≥ 0 kg/s | 0.5 |
| initial_displacement | float | \|x₀\| < 5 m | 0.5 |
| time_step | float | 0.001 ≤ Δt ≤ 0.1 s | 0.01 |
| duration | float | 0 < t ≤ 60 s | 10.0 |
| numerical_method | enum | euler, runge_kutta_2, runge_kutta_4, analytical | runge_kutta_4 |

---

## 6. Endpointy – konfigurácie

### 6.1 POST /api/spring/configurations

**Účel:** Vytvorí a uloží novú konfiguráciu fyzikálneho systému. Nespúšťa simuláciu.

**Request:**
```json
{
  "name": "Slabo tlmený systém",
  "description": "Pružina s malým tlmením pre študijnú ukážku",
  "mass": 1.0,
  "stiffness": 10.0,
  "damping": 0.5,
  "initial_displacement": 0.5,
  "time_step": 0.01,
  "numerical_method": "runge_kutta_4"
}
```

**Success response (201):**
```json
{
  "config_id": "conf_abc123",
  "name": "Slabo tlmený systém",
  "parameters": {
    "mass": 1.0,
    "stiffness": 10.0,
    "damping": 0.5,
    "initial_displacement": 0.5,
    "time_step": 0.01,
    "numerical_method": "runge_kutta_4"
  },
  "characteristics": {
    "period": 2.83,
    "frequency": 0.35,
    "damping_type": "underdamped",
    "damping_ratio": 0.079,
    "natural_frequency": 3.16
  },
  "created_at": "2025-11-08T10:30:00Z"
}
```

**Error response (422):**
```json
{
  "error": "validation_error",
  "message": "Hmotnosť musí byť kladná",
  "details": [{ "field": "mass", "value": -1.0 }]
}
```

---

### 6.2 GET /api/spring/configurations

**Účel:** Vráti zoznam všetkých uložených konfigurácií.

**Query parametre:**
- `damping_type` — filter podľa typu tlmenia (`underdamped`, `overdamped`, `critical`)
- `method` — filter podľa numerickej metódy

**Response (200):**
```json
{
  "configurations": [
    {
      "config_id": "conf_abc123",
      "name": "Slabo tlmený systém",
      "description": "Pružina s malým tlmením",
      "parameters": {
        "mass": 1.0,
        "stiffness": 10.0,
        "damping": 0.5,
        "initial_displacement": 0.5
      },
      "characteristics": {
        "period": 2.83,
        "frequency": 0.35,
        "damping_type": "underdamped"
      },
      "created_at": "2025-11-08T10:30:00Z",
      "times_simulated": 7
    }
  ]
}
```

---

### 6.3 GET /api/spring/configurations/{config_id}

**Účel:** Vráti detail konkrétnej konfigurácie.

**Response (200):** Plný objekt konfigurácie vrátane všetkých charakteristík.

**Error (404):**
```json
{ "error": "not_found", "message": "Konfigurácia conf_xxx neexistuje" }
```

---

### 6.4 PUT /api/spring/configurations/{config_id}

**Účel:** Aktualizuje existujúcu konfiguráciu. Validácia je rovnaká ako pri vytvorení.

**Response (200):**
```json
{ "config_id": "conf_abc123", "status": "updated", "updated_at": "2025-11-08T11:00:00Z" }
```

---

### 6.5 DELETE /api/spring/configurations/{config_id}

**Účel:** Zmaže konfiguráciu. Nie je možné zmazať konfiguráciu, ktorá má práve bežiacu simuláciu.

**Response (200):**
```json
{ "config_id": "conf_abc123", "status": "deleted" }
```

**Error (409):**
```json
{ "error": "conflict", "message": "Konfigurácia má aktívnu simuláciu sim_xyz789" }
```

---

### 6.6 POST /api/spring/configurations/validate

**Účel:** Validácia parametrov bez uloženia konfigurácie.

**Response (200):**
```json
{ "valid": true, "characteristics": { "period": 2.83, "damping_type": "underdamped" } }
```

---

### 6.7 GET /api/spring/configurations/{config_id}/history

**Účel:** Vráti históriu simulácií pre danú konfiguráciu.

---

## 7. Endpointy – simulácie

### 7.1 POST /api/spring/simulations/start

**Účel:** Spustí simuláciu na základe existujúcej konfigurácie.

> **Poznámka:** Backend vytvorí záznam so stavom `pending`. Samotný výpočet sa spustí až v momente, keď sa klient pripojí na WebSocket. Tým sa eliminuje race condition (strata prvých dát).

**Request:**
```json
{
  "config_id": "conf_abc123",
  "duration": 10.0
}
```

**Response (200):**
```json
{
  "simulation_id": "sim_xyz789",
  "config_id": "conf_abc123",
  "config_name": "Slabo tlmený systém",
  "websocket_url": "ws://localhost:8000/ws/sim_xyz789",
  "status": "pending",
  "duration": 10.0,
  "started_at": "2025-11-08T10:35:00Z"
}
```

---

### 7.2 GET /api/spring/simulations

**Účel:** Vráti zoznam simulácií.

**Query parametre:**
- `status` — filter: `pending`, `running`, `completed`, `stopped`
- `config_id` — filter podľa konfigurácie
- `limit` — max. počet výsledkov (default 50)

---

### 7.3 GET /api/spring/simulations/{simulation_id}

**Účel:** Vráti detail konkrétnej simulácie.

---

### 7.4 DELETE /api/spring/simulations/{simulation_id}

**Účel:** Zastaví bežiacu simuláciu.

**Response (200):**
```json
{
  "status": "stopped",
  "simulation_id": "sim_xyz789",
  "elapsed_time": 5.25
}
```

---

## 8. Ďalšie endpointy

| Endpoint | Popis |
|---|---|
| `GET /api/info` | Info o serveri, verzia API, podporované rozsahy parametrov, dostupné metódy |

---

## 9. Chybové kódy

| HTTP kód | Význam |
|---|---|
| 200 | Úspech |
| 201 | Vytvorené |
| 400 | Chybný vstup |
| 404 | Zdroj neexistuje |
| 409 | Konflikt (napr. aktívna simulácia) |
| 422 | Nevalidný formát dát (Pydantic) |
| 500 | Interná chyba servera |

**Štandardný formát chybovej odpovede:**
```json
{
  "error": "validation_error",
  "message": "Popis chyby pre používateľa",
  "details": []
}
```
