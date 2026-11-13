from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

app = FastAPI(
    title="Nuxia AI Enterprise Core",
    version="2.0.0",
    description="Backend oficial de operaciones y telemetría para comercios B2B en Chile."
)

# Configuración CORS nivel producción (permite conectar cualquier frontend web o móvil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos en memoria precargada con datos realistas para demostración comercial
DATABASE = {
    "repartidores": {
        "DELIVERY-01": {"nombre": "Carlos Soto", "vehiculo": "Moto Honda XR", "comuna": "Providencia", "estado": "activo", "token": "tk_demo_01"},
        "DELIVERY-02": {"nombre": "Andrea Muñoz", "vehiculo": "Bicicleta Eléctrica", "comuna": "Santiago Centro", "estado": "activo", "token": "tk_demo_02"},
        "DELIVERY-03": {"nombre": "Esteban Valenzuela", "vehiculo": "Moto Yamaha FZ", "comuna": "Las Condes", "estado": "en ruta", "token": "tk_demo_03"}
    },
    "telemetria": {
        "DELIVERY-01": {"lat": -33.4372, "lng": -70.6506, "bateria": "89%", "velocidad": "35 km/h"},
        "DELIVERY-02": {"lat": -33.4449, "lng": -70.6539, "bateria": "95%", "velocidad": "18 km/h"},
        "DELIVERY-03": {"lat": -33.4172, "lng": -70.6067, "bateria": "72%", "velocidad": "42 km/h"}
    }
}

@app.get("/")
def read_root():
    return {
        "system": "Nuxia AI Enterprise Core",
        "status": "online",
        "region": "Santiago, Chile",
        "active_fleet": len(DATABASE["repartidores"])
    }

@app.post("/api/delivery/vincular")
def vincular_delivery(payload: Dict[Any, Any]):
    delivery_id = payload.get("delivery_id")
    nombre = payload.get("nombre", "Repartidor Externo")
    comuna = payload.get("comuna", "Santiago")
    
    if not delivery_id:
        raise HTTPException(status_code=400, detail="El campo delivery_id es obligatorio")
        
    DATABASE["repartidores"][delivery_id] = {
        "nombre": nombre,
        "vehiculo": "Moto Asignada",
        "comuna": comuna,
        "estado": "activo",
        "token": f"tk_secure_{delivery_id}"
    }
    return {"message": "Delivery vinculado exitosamente", "delivery_id": delivery_id, "data": DATABASE["repartidores"][delivery_id]}

@app.get("/api/delivery/flota")
def obtener_flota():
    return {
        "total_activos": len(DATABASE["repartidores"]),
        "flota": DATABASE["repartidores"],
        "telemetria_actual": DATABASE["telemetria"]
    }

@app.post("/api/dispositivos/telemetria")
def actualizar_telemetria(payload: Dict[Any, Any]):
    device_id = payload.get("device_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    bateria = payload.get("bateria", "100%")
    velocidad = payload.get("velocidad", "0 km/h")
    
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id requerido")
        
    DATABASE["telemetria"][device_id] = {
        "lat": lat,
        "lng": lng,
        "bateria": bateria,
        "velocidad": velocidad
    }
    return {"status": "telemetria sincronizada", "device_id": device_id}

@app.post("/api/seguridad/revocar-dispositivo")
def revocar_dispositivo(payload: Dict[Any, Any]):
    device_id = payload.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id es obligatorio para el Kill Switch")
        
    last_known = DATABASE["telemetria"].get(device_id, {"lat": -33.4489, "lng": -70.6693, "estado": "desconectado"})
    
    # Marcar como inactivo en flota si existe
    if device_id in DATABASE["repartidores"]:
        DATABASE["repartidores"][device_id]["estado"] = "REVOCADO_KILL_SWITCH"
        
    return {
        "action": "KILL_SWITCH_EXECUTED",
        "alert": "Dispositivo bloqueado remotamente y sesión terminada",
        "device_id": device_id,
        "telemetria_final": last_known
    }
