import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, get_db, ConfigurationDB, SimulationDB
from models import (
    ConfigurationCreate,
    ConfigurationUpdate,
    ConfigurationResponse,
    SimulationStart,
    SimulationResponse,
    compute_characteristics,
)

app = FastAPI(
    title="Spring Simulator API",
    description="Real-time damped spring-mass simulation backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WS_HOST = "localhost"
WS_PORT = 9000


@app.on_event("startup")
def startup():
    init_db()


# ── INFO ─────────────────────────────────────────────────────────────────────

@app.get("/api/info")
def get_info():
    return {
        "name": "Spring Simulator",
        "version": "1.0.0",
        "parameter_ranges": {
            "mass": {"min": 0.01, "max": None, "unit": "kg"},
            "stiffness": {"min": 0.01, "max": None, "unit": "N/m"},
            "damping": {"min": 0.0, "max": None, "unit": "kg/s"},
            "initial_displacement": {"min": -4.99, "max": 4.99, "unit": "m"},
            "time_step": {"min": 0.001, "max": 0.1, "unit": "s"},
            "duration": {"min": 0.01, "max": 60.0, "unit": "s"},
        },
        "numerical_methods": ["euler", "runge_kutta_2", "runge_kutta_4", "analytical"],
        "websocket_port": WS_PORT,
    }


# ── CONFIGURATIONS ────────────────────────────────────────────────────────────

@app.post("/api/spring/configurations", response_model=ConfigurationResponse, status_code=201)
def create_configuration(data: ConfigurationCreate, db: Session = Depends(get_db)):
    chars = compute_characteristics(data.mass, data.stiffness, data.damping)
    config_id = f"conf_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    db_config = ConfigurationDB(
        id=config_id,
        name=data.name,
        description=data.description,
        mass=data.mass,
        stiffness=data.stiffness,
        damping=data.damping,
        initial_displacement=data.initial_displacement,
        time_step=data.time_step,
        numerical_method=data.numerical_method,
        period=chars["period"],
        frequency=chars["frequency"],
        damping_type=chars["damping_type"],
        damping_ratio=chars["damping_ratio"],
        created_at=now,
        updated_at=now,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@app.get("/api/spring/configurations", response_model=list[ConfigurationResponse])
def list_configurations(
    damping_type: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ConfigurationDB)
    if damping_type:
        query = query.filter(ConfigurationDB.damping_type == damping_type)
    if method:
        query = query.filter(ConfigurationDB.numerical_method == method)
    return query.order_by(ConfigurationDB.created_at.desc()).all()


@app.get("/api/spring/configurations/{config_id}", response_model=ConfigurationResponse)
def get_configuration(config_id: str, db: Session = Depends(get_db)):
    config = db.query(ConfigurationDB).filter(ConfigurationDB.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@app.put("/api/spring/configurations/{config_id}", response_model=ConfigurationResponse)
def update_configuration(config_id: str, data: ConfigurationUpdate, db: Session = Depends(get_db)):
    config = db.query(ConfigurationDB).filter(ConfigurationDB.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    # Recompute characteristics if physics params changed
    phys_keys = {"mass", "stiffness", "damping"}
    if phys_keys & set(update_data.keys()):
        chars = compute_characteristics(config.mass, config.stiffness, config.damping)
        config.period = chars["period"]
        config.frequency = chars["frequency"]
        config.damping_type = chars["damping_type"]
        config.damping_ratio = chars["damping_ratio"]

    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config


@app.delete("/api/spring/configurations/{config_id}")
def delete_configuration(config_id: str, db: Session = Depends(get_db)):
    config = db.query(ConfigurationDB).filter(ConfigurationDB.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    active = db.query(SimulationDB).filter(
        SimulationDB.config_id == config_id,
        SimulationDB.status == "running"
    ).first()
    if active:
        raise HTTPException(status_code=409, detail="Cannot delete configuration with active simulation")

    db.delete(config)
    db.commit()
    return {"message": "Configuration deleted"}


@app.post("/api/spring/configurations/validate")
def validate_configuration(data: ConfigurationCreate):
    chars = compute_characteristics(data.mass, data.stiffness, data.damping)
    return {"valid": True, "characteristics": chars}


@app.get("/api/spring/configurations/{config_id}/history", response_model=list[SimulationResponse])
def get_configuration_history(config_id: str, db: Session = Depends(get_db)):
    config = db.query(ConfigurationDB).filter(ConfigurationDB.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    sims = db.query(SimulationDB).filter(SimulationDB.config_id == config_id).order_by(SimulationDB.started_at.desc()).all()
    return sims


# ── SIMULATIONS ───────────────────────────────────────────────────────────────

@app.post("/api/spring/simulations/start", response_model=SimulationResponse)
def start_simulation(data: SimulationStart, db: Session = Depends(get_db)):
    config = db.query(ConfigurationDB).filter(ConfigurationDB.id == data.config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    sim_id = f"sim_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    db_sim = SimulationDB(
        id=sim_id,
        config_id=data.config_id,
        status="running",
        duration=data.duration,
        started_at=now,
    )
    db.add(db_sim)
    db.commit()
    db.refresh(db_sim)

    response = SimulationResponse.model_validate(db_sim)
    response.websocket_url = f"ws://{WS_HOST}:{WS_PORT}/ws/{sim_id}"
    return response


@app.get("/api/spring/simulations", response_model=list[SimulationResponse])
def list_simulations(
    status: Optional[str] = Query(None),
    config_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(SimulationDB)
    if status:
        query = query.filter(SimulationDB.status == status)
    if config_id:
        query = query.filter(SimulationDB.config_id == config_id)
    return query.order_by(SimulationDB.started_at.desc()).limit(limit).all()


@app.get("/api/spring/simulations/{sim_id}", response_model=SimulationResponse)
def get_simulation(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(SimulationDB).filter(SimulationDB.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@app.delete("/api/spring/simulations/{sim_id}")
def stop_simulation(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(SimulationDB).filter(SimulationDB.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim.status = "stopped"
    sim.completed_at = datetime.utcnow()
    db.commit()
    return {"message": "Simulation stopped"}
