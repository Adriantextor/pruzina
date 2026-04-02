# Analýza projektu – Simulátor kmitajúcej pružiny so závažím

## 1. Účel dokumentu

Tento dokument obsahuje business analýzu a IT analýzu projektu. Cieľom je:

- definovať účel a rozsah aplikácie,
- identifikovať stakeholderov a ich potreby,
- určiť funkčné a nefunkčné požiadavky,
- navrhnúť architektúru systému na vysokej úrovni.

---

## 2. Business analýza

### 2.1 Business zadanie

> Vytvorte webovú aplikáciu pre real-time simuláciu kmitajúcej pružiny so závažím, ktorá využíva backend v Pythone, frontend v JavaScripte a WebSocket pre jednosmernú komunikáciu v reálnom čase.

### 2.2 Typ projektu

Projekt je **Green Field** riešenie — nová aplikácia bez závislostí na existujúcich systémoch.

### 2.3 Cieľová skupina (Stakeholders)

| Skupina | Potreba |
|---|---|
| Študenti fyziky a informatiky | Pochopenie numerických metód a tlmeného kmitavého pohybu |
| Pedagógovia | Demonštrácia fyzikálneho modelu na vyučovaní |
| Vývojári | Referenčná implementácia REST + WebSocket architektúry |

### 2.4 MVP vs. Atraktívne riešenie

**MVP:**
- Jeden typ numerickej metódy (RK4)
- Základná vizualizácia pružiny (Canvas)
- Spustenie simulácie s pevnými parametrami

**Atraktívne riešenie (zadanie):**
- 4 numerické metódy (Euler, RK2, RK4, analytická)
- Ukladanie konfigurácií do databázy s históriou
- Real-time grafy (výchylka, rýchlosť, fázový diagram, energia)
- Správa konfigurácií (CRUD operácie)

---

## 3. In Scope / Out of Scope

### In Scope
- Simulácia tlmeného harmonického oscilátora (1D)
- Správa konfigurácií fyzikálneho systému (CRUD)
- Real-time vizualizácia cez WebSocket
- História simulácií v databáze
- Minimálne 3 numerické metódy

### Out of Scope
- 3D vizualizácia
- Simulácia systému viacerých spojených pružín
- Autentifikácia a správa používateľov
- Export dát do CSV/JSON (voliteľné rozšírenie)

---

## 4. IT analýza

### 4.1 Komponent diagram HL

```
┌─────────────────────────────────────────────────────────┐
│                        FRONTEND                         │
│  ┌──────────────────────┐  ┌────────────────────────┐   │
│  │  Config Panel        │  │  Simulator UI          │   │
│  │  (frontend/index.html)│  │  (simulator/index.html)│   │
│  └──────────┬───────────┘  └──────────┬─────────────┘   │
└─────────────┼────────────────────────┼─────────────────┘
              │ REST API                │ WebSocket
              ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│                        BACKEND                          │
│  ┌──────────────────┐   ┌──────────────────────────┐    │
│  │  FastAPI          │   │  WebSocket Server        │    │
│  │  REST API         │   │  ws://.../ws/{sim_id}    │    │
│  └────────┬─────────┘   └────────────┬─────────────┘    │
│           │                          │                   │
│  ┌────────▼─────────────────────────▼─────────────┐     │
│  │           Fyzikálny engine                      │     │
│  │   Euler | RK2 | RK4 | Analytická               │     │
│  └────────────────────┬────────────────────────────┘     │
│                       │                                  │
│  ┌────────────────────▼────────────────────────────┐     │
│  │           SQLite + SQLAlchemy ORM               │     │
│  │   configurations | simulations                  │     │
│  └─────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Komunikačný tok (Sequence Diagram HL)

**FÁZA 1 — Vytvorenie konfigurácie**
1. Používateľ vyplní formulár
2. Frontend → `POST /api/spring/configurations`
3. Backend validuje, vypočíta charakteristiky, uloží do DB
4. Backend → Frontend: `config_id` + charakteristiky systému
5. Frontend zobrazí konfiguráciu v zozname

**FÁZA 2 — Správa konfigurácií**
1. Frontend → `GET /api/spring/configurations`
2. Backend → Frontend: zoznam konfigurácií
3. Možnosti: úprava (PUT), mazanie (DELETE), duplikovanie

**FÁZA 3 — Spustenie simulácie**
1. Frontend → `POST /api/spring/simulations/start` (config_id + duration)
2. Backend vytvorí záznam so stavom `pending`, vráti `simulation_id` + `websocket_url`
3. Frontend otvorí WebSocket spojenie
4. Po pripojení klienta backend spustí asynchrónnu simuláciu
5. Server posiela: `setup` → `data` (každých 50ms) → `completed`
6. Frontend vizualizuje dáta v reálnom čase

### 4.3 Technologické rozhodnutia

| Oblasť | Zvolená technológia | Odôvodnenie |
|---|---|---|
| Backend framework | FastAPI (Python) | Asynchrónna podpora, automatická OpenAPI dokumentácia, Pydantic validácia |
| WebSocket | FastAPI WebSocket (natívny) | Všetko na jednom porte (8000), jednoduchší deployment |
| Databáza | SQLite + SQLAlchemy | Bezserverová DB vhodná pre vývoj; ORM umožní migráciu na PostgreSQL |
| Frontend vizualizácia | Canvas API + Chart.js | Natívne API pre animáciu, Chart.js pre grafy |
| Numerika | scipy + vlastný solver | scipy ako referencia, vlastné metódy pre porovnanie |
| Deployment | Docker + docker-compose | Reprodukovateľné prostredie |

### 4.4 Nefunkčné požiadavky

| Požiadavka | Špecifikácia |
|---|---|
| Výkon | WebSocket správy každých 50ms (20 FPS) |
| Stabilita | Podpora viacerých súčasných simulácií |
| Bezpečnosť | Validácia všetkých vstupov, rate limiting |
| Responzívnosť | Mobile-friendly frontend |
| Dostupnosť | Automatické reštartovanie (systemd / Docker restart policy) |
