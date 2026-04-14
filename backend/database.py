from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spring_simulator.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ConfigurationDB(Base):
    __tablename__ = "configurations"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    mass = Column(Float, nullable=False)
    stiffness = Column(Float, nullable=False)
    damping = Column(Float, nullable=False)
    initial_displacement = Column(Float, nullable=False)
    time_step = Column(Float, nullable=False)
    numerical_method = Column(String(50), nullable=False)
    period = Column(Float, nullable=True)
    frequency = Column(Float, nullable=True)
    damping_type = Column(String(20), nullable=True)
    damping_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SimulationDB(Base):
    __tablename__ = "simulations"

    id = Column(String(50), primary_key=True)
    config_id = Column(String(50), ForeignKey("configurations.id"), nullable=False)
    status = Column(String(20), nullable=False, default="running")
    duration = Column(Float, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_steps = Column(Integer, nullable=True)
    final_displacement = Column(Float, nullable=True)
    final_velocity = Column(Float, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()