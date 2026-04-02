# Návrh WebSocket komunikácie

## 1. Účel dokumentu

Tento dokument popisuje návrh WebSocket komunikácie pre projekt Simulátor kmitajúcej pružiny so závažím.

---

## 2. Princípy

- WebSocket je **jednosmerný**: server → klient.
- Klient sa pripojí pomocou `simulation_id` získaného z REST API.
- Samotný výpočet simulácie sa spustí až po pripojení klienta (eliminuje race condition).
- Správy sú posielané vo formáte JSON každých **50ms** (20 FPS).
- WebSocket je implementovaný natívne cez FastAPI — beží na rovnakom porte ako REST API (port 8000).

---

## 3. Endpoint

```
ws://{host}:8000/ws/{simulation_id}
```

---

## 4. Životný cyklus spojenia

```
Klient                              Server
  |                                   |
  |-- POST /simulations/start ------->|
  |<-- { simulation_id, status: pending } --|
  |                                   |
  |-- WS connect /ws/{sim_id} ------->|
  |                                   | ← Tu sa spustí výpočet
  |<-- { type: "setup" } -------------|
  |                                   |
  |<-- { type: "data" } --------------|  každých 50ms
  |<-- { type: "data" } --------------|
  |      ...                          |
  |<-- { type: "completed" } ---------|
  |                                   |
  |-- WS close ---------------------->|
```

Klient môže kedykoľvek ukončiť simuláciu volaním `DELETE /api/spring/simulations/{simulation_id}`.

---

## 5. Formát správ

### 5.1 Setup správa

Poslaná ihneď po pripojení klienta. Obsahuje všetky parametre a charakteristiky systému.

```json
{
  "type": "setup",
  "simulation_id": "sim_xyz789",
  "config_id": "conf_abc123",
  "parameters": {
    "mass": 1.0,
    "stiffness": 10.0,
    "damping": 0.5,
    "initial_displacement": 0.5,
    "time_step": 0.01,
    "method": "runge_kutta_4"
  },
  "characteristics": {
    "period": 2.83,
    "frequency": 0.35,
    "damping_type": "underdamped",
    "damping_ratio": 0.079
  },
  "duration": 10.0
}
```

### 5.2 Data správa

Posielaná každých 50ms počas simulácie.

```json
{
  "type": "data",
  "time": 0.5,
  "displacement": 0.23,
  "velocity": -1.2,
  "acceleration": 3.4,
  "kinetic_energy": 0.72,
  "potential_energy": 0.26,
  "total_energy": 0.98
}
```

### 5.3 Completed správa

Poslaná po dokončení simulácie. Klient zatvorí WebSocket spojenie.

```json
{
  "type": "completed",
  "total_time": 10.0,
  "total_steps": 1000,
  "final_displacement": 0.05,
  "final_velocity": -0.12
}
```

### 5.4 Error správa

Poslaná pri chybe počas simulácie.

```json
{
  "type": "error",
  "message": "Simulácia zlyhala",
  "code": "simulation_error"
}
```

---

## 6. Spracovanie správ na frontende

```javascript
function connectWebSocket(wsUrl) {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch (message.type) {
            case 'setup':
                initializeVisualization(message.parameters, message.characteristics);
                break;
            case 'data':
                updateVisualization(message);
                updateGraphs(message);
                displayValues(message);
                break;
            case 'completed':
                displayFinalResults(message);
                ws.close();
                break;
            case 'error':
                console.error('Simulation error:', message.message);
                ws.close();
                break;
        }
    };

    ws.onerror = (error) => console.error('WebSocket error:', error);
    ws.onclose = () => console.log('WebSocket closed');
}
```

---

## 7. Prenos stavu medzi stránkami

Projekt má dve HTML stránky (`frontend/index.html` a `simulator/index.html`). `simulation_id` sa prenáša cez URL parameter:

```
simulator/index.html?sim_id=sim_xyz789
```

Na strane simulátora:

```javascript
const params = new URLSearchParams(window.location.search);
const simId = params.get('sim_id');
connectWebSocket(`ws://localhost:8000/ws/${simId}`);
```
