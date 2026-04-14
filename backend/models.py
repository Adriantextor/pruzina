from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
import math

NumericalMethod = Literal["euler", "runge_kutta_2", "runge_kutta_4", "analytical"]
DampingType = Literal["undamped", "underdamped", "critical", "overdamped"]
SimulationStatus = Literal["running", "completed", "stopped"]


class ConfigurationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    mass: float
    stiffness: float
    damping: float
    initial_displacement: float
    time_step: float = 0.01
    numerical_method: NumericalMethod = "runge_kutta_4"

    @field_validator("mass", "stiffness")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    @field_validator("damping")
    @classmethod
    def damping_non_negative(cls, v):
        if v < 0:
            raise ValueError("Must be >= 0")
        return v

    @field_validator("initial_displacement")
    @classmethod
    def displacement_range(cls, v):
        if abs(v) >= 5:
            raise ValueError("Must be in range (-5, 5)")
        return v

    @field_validator("time_step")
    @classmethod
    def time_step_range(cls, v):
        if not (0.001 <= v <= 0.1):
            raise ValueError("Must be between 0.001 and 0.1")
        return v


class ConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mass: Optional[float] = None
    stiffness: Optional[float] = None
    damping: Optional[float] = None
    initial_displacement: Optional[float] = None
    time_step: Optional[float] = None
    numerical_method: Optional[NumericalMethod] = None


class ConfigurationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    mass: float
    stiffness: float
    damping: float
    initial_displacement: float
    time_step: float
    numerical_method: str
    period: Optional[float]
    frequency: Optional[float]
    damping_type: Optional[str]
    damping_ratio: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimulationStart(BaseModel):
    config_id: str
    duration: float

    @field_validator("duration")
    @classmethod
    def duration_range(cls, v):
        if not (0 < v <= 60):
            raise ValueError("Duration must be between 0 and 60 seconds")
        return v


class SimulationResponse(BaseModel):
    id: str
    config_id: str
    status: str
    duration: float
    started_at: datetime
    completed_at: Optional[datetime]
    total_steps: Optional[int]
    final_displacement: Optional[float]
    final_velocity: Optional[float]
    websocket_url: Optional[str] = None

    class Config:
        from_attributes = True


class SystemCharacteristics(BaseModel):
    natural_frequency: float
    damping_ratio: float
    period: float
    frequency: float
    damped_frequency: Optional[float]
    damping_type: str


def compute_characteristics(mass: float, stiffness: float, damping: float) -> dict:
    omega0 = math.sqrt(stiffness / mass)
    critical_damping = 2 * math.sqrt(stiffness * mass)
    zeta = damping / critical_damping
    period = (2 * math.pi) / omega0
    frequency = 1.0 / period

    if damping == 0:
        damping_type = "undamped"
    elif damping < critical_damping:
        damping_type = "underdamped"
    elif abs(damping - critical_damping) < 1e-9:
        damping_type = "critical"
    else:
        damping_type = "overdamped"

    omega_d = omega0 * math.sqrt(max(0, 1 - zeta ** 2)) if zeta < 1 else 0.0

    return {
        "natural_frequency": omega0,
        "damping_ratio": zeta,
        "period": period,
        "frequency": frequency,
        "damped_frequency": omega_d,
        "damping_type": damping_type,
    }
