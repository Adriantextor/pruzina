# Dátový model

## 1. Účel dokumentu

Tento dokument popisuje schému databázy pre projekt Simulátor kmitajúcej pružiny so závažím.

---

## 2. Technológia

- **Databáza:** SQLite (vývoj) / PostgreSQL (produkcia)
- **ORM:** SQLAlchemy (asynchrónny režim s `aiosqlite`)
- **Migrácie:** Alembic

Použitie asynchrónneho SQLAlchemy zabezpečuje, že databázové dotazy neblokujú FastAPI event loop počas behu WebSocket streamov.

---

## 3. Schéma

### 3.1 Tabuľka: configurations

Ukladá fyzikálne parametre systému a vypočítané charakteristiky.

```sql
CREATE TABLE configurations (
    id                  VARCHAR(50) PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    mass                FLOAT NOT NULL,
    stiffness           FLOAT NOT NULL,
    damping             FLOAT NOT NULL,
    initial_displacement FLOAT NOT NULL,
    time_step           FLOAT NOT NULL,
    numerical_method    VARCHAR(50) NOT NULL,
    -- Vypočítané charakteristiky (uložené pri vytvorení)
    period              FLOAT,
    frequency           FLOAT,
    damping_type        VARCHAR(20),
    damping_ratio       FLOAT,
    natural_frequency   FLOAT,
    -- Metadáta
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Stĺpec | Typ | Popis |
|---|---|---|
| id | VARCHAR(50) PK | Unikátny identifikátor (napr. `conf_abc123`) |
| name | VARCHAR(200) | Názov konfigurácie |
| description | TEXT | Voliteľný popis |
| mass | FLOAT | Hmotnosť závaží [kg] |
| stiffness | FLOAT | Tuhost pružiny [N/m] |
| damping | FLOAT | Koeficient tlmenia [kg/s] |
| initial_displacement | FLOAT | Počiatočná výchylka [m] |
| time_step | FLOAT | Časový krok simulácie [s] |
| numerical_method | VARCHAR(50) | Metóda: euler / runge_kutta_2 / runge_kutta_4 / analytical |
| period | FLOAT | Vypočítaná perióda kmitania [s] |
| frequency | FLOAT | Vypočítaná frekvencia [Hz] |
| damping_type | VARCHAR(20) | underdamped / critical / overdamped / undamped |
| damping_ratio | FLOAT | ζ = c / (2√(k·m)) |
| natural_frequency | FLOAT | ω₀ = √(k/m) [rad/s] |

---

### 3.2 Tabuľka: simulations

Ukladá históriu spustených simulácií a ich výsledky.

```sql
CREATE TABLE simulations (
    id                  VARCHAR(50) PRIMARY KEY,
    config_id           VARCHAR(50) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    duration            FLOAT NOT NULL,
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP,
    total_steps         INTEGER,
    final_displacement  FLOAT,
    final_velocity      FLOAT,
    FOREIGN KEY (config_id) REFERENCES configurations(id)
);
```

| Stĺpec | Typ | Popis |
|---|---|---|
| id | VARCHAR(50) PK | Unikátny identifikátor (napr. `sim_xyz789`) |
| config_id | VARCHAR(50) FK | Referencia na `configurations.id` |
| status | VARCHAR(20) | `pending` / `running` / `completed` / `stopped` |
| duration | FLOAT | Požadované trvanie simulácie [s] |
| started_at | TIMESTAMP | Čas vytvorenia záznamu |
| completed_at | TIMESTAMP | Čas dokončenia (NULL ak beží) |
| total_steps | INTEGER | Celkový počet krokov |
| final_displacement | FLOAT | Výsledná výchylka [m] |
| final_velocity | FLOAT | Výsledná rýchlosť [m/s] |

---

## 4. Vzťahy

```
configurations (1) ──── (N) simulations
```

Jedna konfigurácia môže byť spustená viackrát s rôznym trvaním. Počet spustení sa vypočítava ako `COUNT(simulations WHERE config_id = ?)`.

---

## 5. Stavy simulácie

```
pending ──► running ──► completed
                   └──► stopped
```

| Stav | Popis |
|---|---|
| pending | Záznam vytvorený, čaká na pripojenie klienta cez WebSocket |
| running | Klient pripojený, výpočet beží |
| completed | Simulácia dokončená prirodzene |
| stopped | Simulácia zastavená používateľom (DELETE) |
