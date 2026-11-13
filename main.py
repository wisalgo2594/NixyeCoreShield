from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI(title="Nuxia AI Enterprise Core", version="2.0")

# Habilitar CORS para que tu index.html local se conecte sin problemas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Datos para la API
class RegistroDeliveryPayload(BaseModel):
    nombre: str
    telefono: str
    tipo_vehiculo: str
    placa_vehiculo: str
    horario_entrada: str
    horario_salida: str

class TelemetriaPayload(BaseModel):
    id_calle: str
    latitud: float
    longitud: float

# Base de datos en memoria para pruebas rápidas
DB_REPARTIDORES = []
DB_DISPOSITIVOS_ACTIVOS = {}

@app.post("/api/delivery/vincular")
def vincular_delivery(payload: RegistroDeliveryPayload, x_nuvio_token: str = Header(...)):
    if x_nuvio_token != "token_demo_comercio":
        raise HTTPException(status_code=401, detail="Token de comercio inválido o QR expirado.")
    
    id_calle_generado = f"REP-{random.randint(1000, 9999)}"
    
    nuevo_repartidor = {
        "id_calle": id_calle_generado,
        "nombre": payload.nombre,
        "telefono": payload.telefono,
        "vehiculo": payload.tipo_vehiculo,
        "placa": payload.placa_vehiculo,
        "entrada": payload.horario_entrada,
        "salida": payload.horario_salida,
        "estado": "Activo",
        "token_sesion": f"sess_{random.randint(100000, 999999)}"
    }
    
    DB_REPARTIDORES.append(nuevo_repartidor)
    
    return {
        "status": "ok",
        "id_calle": id_calle_generado,
        "token_sesion": nuevo_repartidor["token_sesion"],
        "mensaje": f"Repartidor enlazado con ID de calle {id_calle_generado}"
    }

@app.get("/api/delivery/flota")
def obtener_flota(x_nuvio_token: str = Header(...)):
    if x_nuvio_token != "token_demo_comercio":
        raise HTTPException(status_code=401, detail="No autorizado.")
    return {"flota": DB_REPARTIDORES}

@app.post("/api/dispositivos/telemetria")
def actualizar_posicion(payload: TelemetriaPayload):
    DB_DISPOSITIVOS_ACTIVOS[payload.id_calle] = {
        "lat": payload.latitud,
        "lng": payload.longitud,
        "ultima_senal": "Activa ahora"
    }
    return {"status": "actualizado"}

@app.post("/api/seguridad/revocar-dispositivo")
def desenlazar_dispositivo(id_calle: str, x_nuvio_token: str = Header(...)):
    if x_nuvio_token != "token_demo_comercio":
        raise HTTPException(status_code=401, detail="No autorizado.")
    
    ultima_pos = DB_DISPOSITIVOS_ACTIVOS.get(id_calle, {"lat": -33.4489, "lng": -70.6693, "ultima_senal": "Desconocida"})
    
    # Remover de activos o marcar revocado
    global DB_REPARTIDORES
    DB_REPARTIDORES = [r for r in DB_REPARTIDORES if r["id_calle"] != id_calle]
    
    return {
        "status": "revocado",
        "mensaje": f"Dispositivo {id_calle} desenlazado por seguridad.",
        "ultima_ubicacion_registrada": ultima_pos
    }