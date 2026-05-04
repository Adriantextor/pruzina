# Simulátor pružiny — Matematika & Parametre

## Fyzikálny model

Tlmený harmonický oscilátor:

```
m·ẍ + c·ẋ + k·x = 0
```

Pre numerické riešenie rozložené na dve rovnice 1. rádu:

```
dx/dt = v
dv/dt = -(c/m)·v - (k/m)·x
```

---

## Vstupné parametre — rozsahy

| Parameter | Min | Max | Predvolená | Jednotka |
|-----------|-----|-----|-----------|----------|
| Hmotnosť `m` | > 0 | ∞ | 1.0 | kg |
| Tuhost `k` | > 0 | ∞ | 10.0 | N/m |
| Tlmenie `c` | ≥ 0 | ∞ | 0.5 | kg/s |
| Počiatočná výchylka `x₀` | > −5.0 | < 5.0 | 0.5 | m |
| Časový krok `Δt` | 0.001 | 0.1 | 0.01 | s |
| Trvanie simulácie | > 0 | 60.0 | 10.0 | s |

> Počiatočná rýchlosť je vždy `v₀ = 0`.

---

## Odvodené charakteristiky (automaticky vypočítané)

| Veličina | Vzorec |
|----------|--------|
| Prirodzená frekvencia | `ω₀ = √(k/m)` |
| Kritické tlmenie | `c_crit = 2·√(k·m)` |
| Pomer tlmenia | `ζ = c / c_crit` |
| Perióda | `T = 2π / ω₀` |
| Frekvencia | `f = 1 / T` |
| Tlmená frekvencia | `ω_d = ω₀·√(1 − ζ²)` (len pre ζ < 1) |

### Typy tlmenia

| Typ | Podmienka |
|-----|-----------|
| Netlmené | ζ = 0 |
| Podkritické | 0 < ζ < 1 |
| Kritické | ζ = 1 |
| Nadkritické | ζ > 1 |

---

## Numerické metódy

### Euler (1. rád)
```
x' = x + Δt·v
v' = v + Δt·(-(c/m)·v - (k/m)·x)
```

### Runge-Kutta 2 (2. rád)
```
k1 = derivatives(x, v)
k2 = derivatives(x + Δt/2·k1)
(x', v') = (x, v) + Δt·k2
```

### Runge-Kutta 4 (4. rád) — predvolená
```
k1 = derivatives(x, v)
k2 = derivatives(x + Δt/2·k1)
k3 = derivatives(x + Δt/2·k2)
k4 = derivatives(x + Δt·k3)
(x', v') = (x, v) + (Δt/6)·(k1 + 2k2 + 2k3 + k4)
```

### Analytická — len pre ζ < 1
```
x(t) = x₀·exp(-ζ·ω₀·t)·[cos(ω_d·t) + (ζ·ω₀/ω_d)·sin(ω_d·t)]
```

---

## Energia

```
E_kinetická   = ½·m·v²
E_potenciálna = ½·k·x²
E_celková     = E_k + E_p
```

Pri tlmení (c > 0) celková energia monotónne klesá. Pri c = 0 zostáva konštantná.