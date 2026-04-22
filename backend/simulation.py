import math
from typing import Generator, Tuple


def _derivatives(x: float, v: float, mass: float, stiffness: float, damping: float) -> Tuple[float, float]:
    """Returns (dx/dt, dv/dt) for the damped spring-mass system."""
    dxdt = v
    dvdt = -(damping / mass) * v - (stiffness / mass) * x
    return dxdt, dvdt


def euler_step(x: float, v: float, dt: float, mass: float, stiffness: float, damping: float) -> Tuple[float, float]:
    dx, dv = _derivatives(x, v, mass, stiffness, damping)
    return x + dt * dx, v + dt * dv


def runge_kutta_2_step(x: float, v: float, dt: float, mass: float, stiffness: float, damping: float) -> Tuple[float, float]:
    k1x, k1v = _derivatives(x, v, mass, stiffness, damping)
    mid_x = x + 0.5 * dt * k1x
    mid_v = v + 0.5 * dt * k1v
    k2x, k2v = _derivatives(mid_x, mid_v, mass, stiffness, damping)
    return x + dt * k2x, v + dt * k2v


def runge_kutta_4_step(x: float, v: float, dt: float, mass: float, stiffness: float, damping: float) -> Tuple[float, float]:
    k1x, k1v = _derivatives(x, v, mass, stiffness, damping)
    k2x, k2v = _derivatives(x + 0.5 * dt * k1x, v + 0.5 * dt * k1v, mass, stiffness, damping)
    k3x, k3v = _derivatives(x + 0.5 * dt * k2x, v + 0.5 * dt * k2v, mass, stiffness, damping)
    k4x, k4v = _derivatives(x + dt * k3x, v + dt * k3v, mass, stiffness, damping)
    new_x = x + (dt / 6) * (k1x + 2 * k2x + 2 * k3x + k4x)
    new_v = v + (dt / 6) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return new_x, new_v


def analytical_step(t: float, x0: float, mass: float, stiffness: float, damping: float) -> Tuple[float, float]:
    """Analytical solution for underdamped system. x0 assumed as initial displacement, v0=0."""
    omega0 = math.sqrt(stiffness / mass)
    critical = 2 * math.sqrt(stiffness * mass)
    zeta = damping / critical

    if zeta >= 1.0:
        raise ValueError("Analytical method only valid for underdamped systems (zeta < 1)")

    omega_d = omega0 * math.sqrt(1 - zeta ** 2)
    A = x0
    decay = math.exp(-zeta * omega0 * t)
    x = decay * (A * math.cos(omega_d * t) + (zeta * omega0 * A / omega_d) * math.sin(omega_d * t))
    v = (decay * (-zeta * omega0) * (A * math.cos(omega_d * t) + (zeta * omega0 * A / omega_d) * math.sin(omega_d * t))
         + decay * ((-A * omega_d * math.sin(omega_d * t)) + (zeta * omega0 * A / omega_d) * omega_d * math.cos(omega_d * t)))
    return x, v


def compute_energies(x: float, v: float, mass: float, stiffness: float) -> dict:
    kinetic = 0.5 * mass * v ** 2
    potential = 0.5 * stiffness * x ** 2
    return {
        "kinetic_energy": kinetic,
        "potential_energy": potential,
        "total_energy": kinetic + potential,
    }


def simulate(
    mass: float,
    stiffness: float,
    damping: float,
    initial_displacement: float,
    time_step: float,
    duration: float,
    method: str,
) -> Generator[dict, None, None]:
    """
    Generator that yields simulation state dicts step by step.
    Each dict contains: time, displacement, velocity, acceleration, energies.
    """
    x = initial_displacement
    v = 0.0
    t = 0.0
    step = 0

    while t <= duration:
        acc = -(damping / mass) * v - (stiffness / mass) * x
        energies = compute_energies(x, v, mass, stiffness)

        yield {
            "time": round(t, 6),
            "displacement": x,
            "velocity": v,
            "acceleration": acc,
            **energies,
            "step": step,
        }

        if method == "euler":
            x, v = euler_step(x, v, time_step, mass, stiffness, damping)
        elif method == "runge_kutta_2":
            x, v = runge_kutta_2_step(x, v, time_step, mass, stiffness, damping)
        elif method == "runge_kutta_4":
            x, v = runge_kutta_4_step(x, v, time_step, mass, stiffness, damping)
        elif method == "analytical":
            t_next = t + time_step
            x, v = analytical_step(t_next, initial_displacement, mass, stiffness, damping)
        else:
            raise ValueError(f"Unknown method: {method}")

        t += time_step
        step += 1
