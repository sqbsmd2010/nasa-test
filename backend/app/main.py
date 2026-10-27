import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import nasa
from .sim import Sim

app = FastAPI(title="OUTPOST backend")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/space-weather")
async def space_weather():
    return await nasa.solar_flares()


@app.get("/api/apod")
async def apod():
    return await nasa.apod()


@app.get("/api/epic")
async def epic():
    return await nasa.epic_latest()


@app.websocket("/ws/sim")
async def sim_ws(ws: WebSocket):
    await ws.accept()
    sim = Sim()
    try:
        flares = await nasa.solar_flares()
        if flares:
            sim.inject_real_flare()
    except Exception:
        pass  # offline-safe: the game must never break if NASA is down
    try:
        while True:
            # player controls arrive as JSON; the sim ticks every 2 s
            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=2.0)
                sim.set_controls(msg.get("alloc", sim.s.alloc), msg.get("shield_m", sim.s.shield_m))
            except asyncio.TimeoutError:
                sim.step()
            await ws.send_json({"telemetry": sim.telemetry()})
    except WebSocketDisconnect:
        pass
