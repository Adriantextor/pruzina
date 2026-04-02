# Infraštruktúra a nasadenie

## 1. Účel dokumentu

Tento dokument popisuje infraštruktúrnu architektúru a spôsob nasadenia projektu Simulátor kmitajúcej pružiny so závažím.

---

## 2. Prostredia

| Prostredie | Konfigurácia | Databáza | Dostupnosť |
|---|---|---|---|
| TEST (lokálne) | localhost, port 8000 | SQLite (súbor) | Len vývojár (localhost) |
| PROD (VPS/cloud) | verejná IP, reverse proxy | SQLite / PostgreSQL | Verejne dostupné |

---

## 3. Porty a sieťová konfigurácia

Celá aplikácia beží na **jedinom porte 8000** — FastAPI obsluhuje REST API aj WebSocket natívne.

| Služba | Port | Protokol | Popis |
|---|---|---|---|
| FastAPI (REST + WebSocket) | 8000 | HTTP / WS | REST API + WebSocket stream |
| Frontend (statické súbory) | 8000 | HTTP | Servované cez FastAPI StaticFiles |

---

## 4. Docker architektúra

Aplikácia je zabalená do Docker kontajnerov spravovaných cez `docker-compose`:

```yaml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data   # perzistentná SQLite databáza
    restart: always

  frontend:
    # Statické súbory sú servované priamo cez FastAPI StaticFiles
    # Nie je potrebný samostatný Nginx kontajner
```

---

## 5. systemd služba (produkčné nasadenie bez Dockeru)

Pre produkčné nasadenie priamo na serveri je k dispozícii `spring.service`:

```ini
[Unit]
Description=Spring Simulator Backend
After=network.target

[Service]
ExecStart=/usr/bin/python3 main.py
WorkingDirectory=/opt/spring-simulator
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Nasadenie:
```bash
sudo cp spring.service /etc/systemd/system/
sudo systemctl enable spring
sudo systemctl start spring
```

---

## 6. Štruktúra repozitára

```
spring-simulator/
├── backend/
│   ├── main.py               # Vstupný bod — spúšťa FastAPI server
│   ├── restapi_server.py     # FastAPI endpointy (konfigurácie, simulácie)
│   ├── websocket_server.py   # WebSocket handler
│   ├── simulation.py         # Fyzikálny engine (Euler, RK2, RK4, analytická)
│   ├── database.py           # SQLAlchemy modely + DB operácie
│   └── models.py             # Pydantic modely pre validáciu API
├── frontend/
│   └── index.html            # Správa konfigurácií (formulár, zoznam, CRUD)
├── simulator/
│   └── index.html            # Vizualizácia simulácie (Canvas, Chart.js, WebSocket)
├── doc/
│   ├── README.md
│   ├── analyza.md
│   ├── fyzikalny_model.md
│   ├── api.md
│   ├── websocket.md
│   ├── datovy_model.md
│   ├── frontend.md
│   ├── infrastruktura.md
│   └── bezpecnost.md
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── _flake8
├── spring.service
└── README.md
```

---

## 7. CI/CD pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.13' }
      - run: pip install flake8
      - run: flake8 backend/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest tests/
```
