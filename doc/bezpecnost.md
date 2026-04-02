# Bezpečnostné požiadavky

## 1. Účel dokumentu

Tento dokument popisuje bezpečnostné požiadavky projektu Simulátor kmitajúcej pružiny so závažím.

---

## 2. Prehľad opatrení

| Hrozba | Opatrenie | Implementácia |
|---|---|---|
| SQL Injection | Parameterizované dotazy | SQLAlchemy ORM — priame SQL zakázané |
| XSS | Escape výstupov | Frontend nestorí raw HTML z API |
| CSRF | CORS konfigurácia | FastAPI CORS middleware — whitelist origins |
| Rate limiting | Obmedzenie požiadaviek | Slowapi — max 100 req/min na IP |
| Validácia ID | Regex validácia | Pydantic — kontrola formátu pred DB dotazom |
| Citlivé údaje | `.env` súbor | python-dotenv, `.gitignore` obsahuje `.env` |
| HTTPS/WSS | TLS v produkcii | Natívna podpora v produkcii |

---

## 3. Validácia vstupov

Všetky vstupy sú validované Pydantic modelmi na strane backendu. Frontend robí len orientačnú validáciu pre UX — backend je autoritatívny zdroj pravdy.

```python
from pydantic import BaseModel, Field

class ConfigurationCreate(BaseModel):
    name: str
    mass: float = Field(gt=0)
    stiffness: float = Field(gt=0)
    damping: float = Field(ge=0)
    initial_displacement: float = Field(gt=-5, lt=5)
    time_step: float = Field(ge=0.001, le=0.1)
    numerical_method: str
```

---

## 4. Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/spring/simulations/start")
@limiter.limit("10/minute")
async def start_simulation(...):
    ...
```

---

## 5. CORS konfigurácia

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # V produkcii konkrétna doména
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)
```

---

## 6. Citlivé údaje

Všetky konfiguračné premenné (databázové URL, secret key) sú uložené v `.env` súbore:

```
DATABASE_URL=sqlite+aiosqlite:///./data/spring.db
SECRET_KEY=...
```

`.env` je zaradený do `.gitignore` — nesmie byť commitnutý do repozitára.
