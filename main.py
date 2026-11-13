from fastapi import FastAPI, HTTPException
from typing import Dict, Any

app = FastAPI(title="Nuxia AI Enterprise Core", version="1.0.0")

# Base de datos en memoria para la preventa
DATABASE = {
    "repartidores": {},
    "telemetria": {}
}

@app.get("/")
def read_root():
    return {"system": "Nuxia AI Core Online", "status": "active"}

@app.post("/api/delivery/vincular")
def vincular_delivery(payload: Dict[Any, Any]):
    delivery_id = payload.get("delivery_id")
    if not delivery_id:
        raise HTTPException(status_code=400, detail="delivery_id es obligatorio")
    DATABASE["repartidores"][delivery_id] = {"estado": "activo", "token": "token_demo_" + delivery_id}
    return {"message": "Delivery vinculado exitosamente", "delivery_id": delivery_id}

@app.get("/api/delivery/flota")
def obtener_flota():
    return {"flota": DATABASE["repartidores"]}

@app.post("/api/dispositivos/telemetria")
def actualizar_telemetria(payload: Dict[Any, Any]):
    device_id = payload.get("device_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    DATABASE["telemetria"][device_id] = {"lat": lat, "lng": lng}
    return {"status": "telemetria actualizada", "device_id": device_id}

@app.post("/api/seguridad/revocar-dispositivo")
def revocar_dispositivo(payload: Dict[Any, Any]):
    device_id = payload.get("device_id")
    if device_id in DATABASE["telemetria"]:
        posicion = DATABASE["telemetria"][device_id]
        return {"action": "KILL_SWITCH_EXECUTED", "device_id": device_id, "last_known_gps": posicion}
    return {"action": "KILL_SWITCH_EXECUTED", "device_id": device_id, "last_known_gps": {"lat": -33.4489, "lng": -70.6693}}
    
    return {
        "status": "revocado",
        "mensaje": f"Dispositivo {id_calle} desenlazado por seguridad.",
        "ultima_ubicacion_registrada": ultima_pos
    }
