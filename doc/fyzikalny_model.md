# Fyzikálny model a numerické metódy

## 1. Účel dokumentu

Tento dokument popisuje fyzikálny model tlmeného harmonického oscilátora a spôsob jeho numerického riešenia v projekte Simulátor kmitajúcej pružiny so závažím.

---

## 2. Diferenciálna rovnica

Tlmený harmonický oscilátor je opísaný rovnicou druhého rádu:

```
m·ẍ + c·ẋ + k·x = 0
```

kde:

| Symbol | Popis | Jednotka |
|---|---|---|
| m | hmotnosť závaží | kg |
| c | koeficient tlmenia | kg/s |
| k | tuhost pružiny | N/m |
| x | výchylka od rovnovážnej polohy | m |

Pre numerické riešenie sa rovnica prevedie na sústavu dvoch rovníc 1. rádu:

```
dx/dt = v
dv/dt = -(c/m)·v - (k/m)·x
```

---

## 3. Typy tlmenia

| Typ | Podmienka | Pohyb |
|---|---|---|
| Podkritické (underdamped) | c < 2√(k·m) | Kmitavý pohyb s klesajúcou amplitúdou |
| Kritické (critically damped) | c = 2√(k·m) | Najrýchlejší návrat bez kmitania |
| Nadkritické (overdamped) | c > 2√(k·m) | Pomalý aperiodický návrat do rovnováhy |
| Netlmené (undamped) | c = 0 | Kmitavý pohyb s konštantnou amplitúdou |

---

## 4. Charakteristiky systému

Tieto hodnoty sa vypočítavajú automaticky pri uložení každej konfigurácie:

| Charakteristika | Vzorec | Jednotka |
|---|---|---|
| Prirodzená kruhová frekvencia | ω₀ = √(k/m) | rad/s |
| Koeficient tlmenia | ζ = c / (2√(k·m)) | bezrozmerný |
| Perióda kmitania | T = 2π / ω₀ | s |
| Frekvencia | f = 1/T | Hz |
| Tlmená kruhová frekvencia | ω_d = ω₀·√(1-ζ²) | rad/s |

---

## 5. Numerické metódy

### 5.1 Prehľad

| Metóda | Kľúč | Presnosť | Vyhodnotenia/krok | Poznámka |
|---|---|---|---|---|
| Eulerova | `euler` | 1. rád | 1 | Najjednoduchšia, kumulácia chyby |
| Runge-Kutta 2 | `runge_kutta_2` | 2. rád | 2 | Midpoint method |
| Runge-Kutta 4 | `runge_kutta_4` | 4. rád | 4 | Predvolená — najlepší kompromis |
| Analytická | `analytical` | presná | 0 | Len pre podkritické tlmenie |

### 5.2 Eulerova metóda

```python
x_new = x + v * dt
v_new = v + (-(c/m)*v - (k/m)*x) * dt
```

### 5.3 Runge-Kutta 4. rádu

```python
def derivatives(x, v):
    return v, -(c/m)*v - (k/m)*x

k1x, k1v = derivatives(x, v)
k2x, k2v = derivatives(x + dt/2*k1x, v + dt/2*k1v)
k3x, k3v = derivatives(x + dt/2*k2x, v + dt/2*k2v)
k4x, k4v = derivatives(x + dt*k3x,   v + dt*k3v)

x_new = x + (dt/6) * (k1x + 2*k2x + 2*k3x + k4x)
v_new = v + (dt/6) * (k1v + 2*k2v + 2*k3v + k4v)
```

### 5.4 Analytické riešenie (len podkritické tlmenie)

```
x(t) = A · exp(-ζ·ω₀·t) · cos(ω_d·t + φ)
```

kde A a φ sú určené z počiatočných podmienok x(0) a v(0).

---

## 6. Implementačný vzor — Python generátor

Fyzikálny engine je implementovaný ako asynchrónny Python generátor. Tento prístup zabezpečuje, že simulácia neblokuje event loop a dáta sú posielané cez WebSocket plynule každých 50ms:

```python
async def simulate(config, duration):
    x = config.initial_displacement
    v = 0.0
    t = 0.0

    while t <= duration:
        x, v = rk4_step(x, v, config)
        a = -(config.damping/config.mass)*v - (config.stiffness/config.mass)*x

        yield {
            "type": "data",
            "time": round(t, 4),
            "displacement": round(x, 6),
            "velocity": round(v, 6),
            "acceleration": round(a, 6),
            "kinetic_energy": round(0.5 * config.mass * v**2, 6),
            "potential_energy": round(0.5 * config.stiffness * x**2, 6),
        }

        await asyncio.sleep(0.05)
        t += config.time_step
```

---

## 7. Validácia vstupných parametrov

| Parameter | Podmienka | Dôvod |
|---|---|---|
| mass | > 0 | Fyzikálna zmysluplnosť |
| stiffness | > 0 | Fyzikálna zmysluplnosť |
| damping | ≥ 0 | Záporné tlmenie nemá fyzikálny zmysel |
| initial_displacement | \|x₀\| < 5 m | Realistická výchylka |
| time_step | 0.001 ≤ Δt ≤ 0.1 s | Numerická stabilita |
| duration | 0 < t ≤ 60 s | Rozumné trvanie simulácie |
