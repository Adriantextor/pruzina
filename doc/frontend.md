# Analýza používateľského rozhrania (UI)

## 1. Účel dokumentu

Tento dokument popisuje štruktúru a správanie frontendu pre projekt Simulátor kmitajúcej pružiny so závažím.

---

## 2. Štruktúra súborov

| Súbor | Funkcia |
|---|---|
| `frontend/index.html` | Správa konfigurácií — formulár, zoznam, CRUD operácie, história |
| `simulator/index.html` | Vizualizácia simulácie — Canvas animácia, grafy, WebSocket klient |

### Prenos stavu medzi stránkami

`simulation_id` sa prenáša cez URL parameter:

```
simulator/index.html?sim_id=sim_xyz789
```

---

## 3. Sekcie používateľského rozhrania

### Sekcia 1 — Formulár novej konfigurácie (`frontend/index.html`)

Formulár obsahuje:
- Názov konfigurácie (povinný)
- Popis (voliteľný)
- Hmotnosť závaží [kg] — default 1.0
- Tuhost pružiny [N/m] — default 10.0
- Koeficient tlmenia [kg/s] — default 0.5
- Počiatočná výchylka [m] — default 0.5
- Časový krok simulácie [s] — default 0.01
- Numerická metóda — dropdown (Euler, RK2, RK4, Analytická)

Po uložení sa zobrazia vypočítané charakteristiky:
- Perióda a frekvencia
- Typ tlmenia
- Koeficient tlmenia ζ

### Sekcia 2 — Zoznam konfigurácií (`frontend/index.html`)

Pre každú konfiguráciu:
- Názov, popis, základné parametre (m, k, c, x₀)
- Charakteristiky (perióda, typ tlmenia)
- Počet spustení
- Tlačidlá: **Spustiť simuláciu**, Upraviť, Zmazať, Duplikovať

Možnosti:
- Filter podľa typu tlmenia a numerickej metódy
- Zoradenie podľa názvu, dátumu, počtu spustení

### Sekcia 3 — Nastavenie simulácie (`frontend/index.html`)

- Výber konfigurácie
- Nastavenie trvania simulácie [s] — default 10.0
- Tlačidlo **Spustiť simuláciu** → redirect na `simulator/index.html?sim_id=...`

### Sekcia 4 — Vizualizácia simulácie (`simulator/index.html`)

**Canvas animácia:**
- Pružina vykreslená sínusovým tvarom závitov
- Závaž sa pohybuje vertikálne podľa `displacement`
- Farba pružiny reflektuje typ tlmenia
- Zobrazenie rovnovážnej polohy (prerušovaná čiara)

**Zobrazenie aktuálnych hodnôt:**
- Čas [s]
- Výchylka [m]
- Rýchlosť [m/s]
- Akcelerácia [m/s²]
- Kinetická, potenciálna a celková energia [J]

**Grafy (Chart.js):**

| Graf | Os X | Os Y | Poznámka |
|---|---|---|---|
| Výchylka v čase | Čas [s] | x [m] | Hlavný graf pohybu |
| Rýchlosť v čase | Čas [s] | v [m/s] | Derivácia výchylky |
| Fázový diagram | x [m] | v [m/s] | Elipsa / špiráľa |
| Energia v čase | Čas [s] | E [J] | Kinetická + potenciálna |

**Ovládanie:**
- Tlačidlo **Stop** (zastaví simuláciu)
- Tlačidlo **Reset** (vráti sa na výber konfigurácie)

### Sekcia 5 — História simulácií (`frontend/index.html`)

- Zoznam posledných simulácií s filtrom podľa konfigurácie
- Možnosť porovnania výsledkov

---

## 4. Workflow používateľa

```
1. Vyplniť formulár → Uložiť konfiguráciu
        ↓
2. Konfigurácia sa zobrazí v zozname
        ↓
3. Kliknúť "Spustiť simuláciu" → Nastaviť trvanie
        ↓
4. Redirect na simulator/index.html?sim_id=...
        ↓
5. WebSocket spojenie → Real-time vizualizácia
        ↓
6. type: "completed" → Výsledky + zatvorenie spojenia
```

---

## 5. Canvas vizualizácia pružiny

```javascript
function drawSpring(displacement) {
    const coils = 10;
    const startY = 50;
    const height = 200 + displacement * 100;
    const centerX = canvas.width / 2;
    const amplitude = 15;

    ctx.beginPath();
    for (let i = 0; i <= coils * 10; i++) {
        const t = i / (coils * 10);
        const y = startY + t * height;
        const x = centerX + amplitude * Math.sin(t * coils * 2 * Math.PI);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Závaž
    ctx.fillRect(centerX - 20, startY + height, 40, 30);
}
```

---

## 6. Responzívnosť

- Flexbox/Grid layout pre rôzne veľkosti obrazoviek
- Canvas sa škáluje podľa dostupnej šírky
- Grafy sa prispôsobujú šírke kontajnera (Chart.js `responsive: true`)
- Mobile-friendly formuláre (veľké vstupy, dostatočný spacing)
