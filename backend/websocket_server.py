import asyncio
import json
import websockets
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, ConfigurationDB, SimulationDB
from simulation import simulate
from models import compute_characteristics

WS_HOST = "0.0.0.0"
WS_PORT = 9001
SEND_INTERVAL = 0.05          # 50ms → 20 FPS
STEPS_PER_FRAME = None        # computed dynamically


async def handle_simulation(websocket, simulation_id: str):
    db: Session = SessionLocal()
    try:
        sim = db.query(SimulationDB).filter(SimulationDB.id == simulation_id).first()
        if not sim:
            await websocket.send(json.dumps({"type": "error", "message": "Simulation not found", "code": 404}))
            return

        if sim.status != "running":
            await websocket.send(json.dumps({"type": "error", "message": "Simulation is not running", "code": 409}))
            return

        config = db.query(ConfigurationDB).filter(ConfigurationDB.id == sim.config_id).first()
        if not config:
            await websocket.send(json.dumps({"type": "error", "message": "Configuration not found", "code": 404}))
            return

        chars = compute_characteristics(config.mass, config.stiffness, config.damping)

        # ── SETUP message ──────────────────────────────────────────────────
        await websocket.send(json.dumps({
            "type": "setup",
            "simulation_id": sim.id,
            "config_id": config.id,
            "parameters": {
                "mass": config.mass,
                "stiffness": config.stiffness,
                "damping": config.damping,
                "initial_displacement": config.initial_displacement,
                "time_step": config.time_step,
                "numerical_method": config.numerical_method,
            },
            "characteristics": chars,
            "duration": sim.duration,
        }))

        # ── DATA messages ──────────────────────────────────────────────────
        # Batch steps so we send every SEND_INTERVAL wall-clock seconds
        steps_per_send = max(1, int(SEND_INTERVAL / config.time_step))

        gen = simulate(
            mass=config.mass,
            stiffness=config.stiffness,
            damping=config.damping,
            initial_displacement=config.initial_displacement,
            time_step=config.time_step,
            duration=sim.duration,
            method=config.numerical_method,
        )

        last_state = None
        total_steps = 0
        buffer = []

        for state in gen:
            # Check if client disconnected or simulation was stopped (re-query every ~1s)
            if total_steps % steps_per_send == 0:
                db.refresh(sim)
                if sim.status != "running":
                    break

            buffer.append(state)
            last_state = state
            total_steps += 1

            if len(buffer) >= steps_per_send:
                # Send the last state in the batch as the data frame
                frame = buffer[-1]
                try:
                    await websocket.send(json.dumps({
                        "type": "data",
                        "time": frame["time"],
                        "displacement": frame["displacement"],
                        "velocity": frame["velocity"],
                        "acceleration": frame["acceleration"],
                        "kinetic_energy": frame["kinetic_energy"],
                        "potential_energy": frame["potential_energy"],
                        "total_energy": frame["total_energy"],
                    }))
                except websockets.exceptions.ConnectionClosed:
                    break
                buffer = []
                await asyncio.sleep(SEND_INTERVAL)

        # ── COMPLETED message ──────────────────────────────────────────────
        if last_state and sim.status == "running":
            sim.status = "completed"
            sim.completed_at = datetime.utcnow()
            sim.total_steps = total_steps
            sim.final_displacement = last_state["displacement"]
            sim.final_velocity = last_state["velocity"]
            db.commit()

            try:
                await websocket.send(json.dumps({
                    "type": "completed",
                    "total_time": last_state["time"],
                    "total_steps": total_steps,
                    "final_displacement": last_state["displacement"],
                    "final_velocity": last_state["velocity"],
                }))
            except websockets.exceptions.ConnectionClosed:
                pass

    except Exception as e:
        try:
            await websocket.send(json.dumps({"type": "error", "message": str(e), "code": 500}))
        except Exception:
            pass
    finally:
        db.close()


async def ws_handler(websocket):
    path = websocket.request.path if hasattr(websocket, "request") else websocket.path
    parts = path.strip("/").split("/")
    # Expected path: /ws/{simulation_id}
    if len(parts) == 2 and parts[0] == "ws":
        simulation_id = parts[1]
        await handle_simulation(websocket, simulation_id)
    else:
        await websocket.send(json.dumps({"type": "error", "message": "Invalid path", "code": 400}))


async def start_websocket_server():
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        print(f"WebSocket server running on ws://{WS_HOST}:{WS_PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(start_websocket_server())
