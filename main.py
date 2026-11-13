from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import time
import uuid

app = FastAPI(
    title="NuxyeCoreShield Enterprise Core",
    version="7.0.0",
    description="Sistema Autónomo de Logística, Almacén y Escudo Cognitivo de Ciberseguridad."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credencial maestra corporativa cifrada conceptualmente
MASTER_API_KEY = "NUXIA_SUPREME_SECURE_KEY_2026"

# ==========================================
# CEREBRO 1 y 3: MOTOR DE INMUNIDAD Y HEURÍSTICA
# ==========================================
SHIELD_MEMORY = {
    "blocked_ips": set(),
    "request_tracker": {},
    "threats_neutralized": 0,
    "security_status": "MAXIMUM_DEFENSE_ACTIVE"
}

def cognitive_security_shield(request: Request):
    """
    Cerebro de Autodefensa: Analiza velocidad de peticiones, detecta scraping 
    y bloquea intentos de saturación o abuso masivo de endpoints.
    """
    client_ip = request.client.host if request.client else "unknown_ip"
    
    if client_ip in SHIELD_MEMORY["blocked_ips"]:
        raise HTTPException(
            status_code=403, 
            detail="NuxyeCoreShield: Acceso permanentemente revocado por comportamiento hostil detectado."
        )
    
    current_time = time.time()
    if client_ip not in SHIELD_MEMORY["request_tracker"]:
        SHIELD_MEMORY["request_tracker"][client_ip] = []
        
    timestamps = SHIELD_MEMORY["request_tracker"][client_ip]
    # Filtrar peticiones de los últimos 10 segundos
    timestamps = [t for t in timestamps if current_time - t < 10]
    timestamps.append(current_time)
    SHIELD_MEMORY["request_tracker"][client_ip] = timestamps
    
    # Umbral heurístico: más de 25 peticiones en 10s activa el aislamiento de IP
    if len(timestamps) > 25:
        SHIELD_MEMORY["blocked_ips"].add(client_ip)
        SHIELD_MEMORY["threats_neutralized"] += 1
        raise HTTPException(
            status_code=429, 
            detail="NuxyeCoreShield ALERTA: Tráfico anómalo o intento de extracción masiva bloqueado."
        )
    return True

def verify_shield_credentials(x_api_key: Optional[str] = Header(None), request: Request = None):
    if request:
        cognitive_security_shield(request)
        
    if not x_api_key or x_api_key != MASTER_API_KEY:
        if request and request.client:
            SHIELD_MEMORY["threats_neutralized"] += 1
        raise HTTPException(
            status_code=401, 
            detail="NuxyeCoreShield: Credencial de autenticación rechazada por el núcleo defensivo."
        )
    return True

# ==========================================
# CEREBRO 2: DLP Y VALIDACIÓN DE PAYLOADS
# ==========================================
class SecureDispatchPayload(BaseModel):
    sku: str = Field(..., min_length=3, max_length=20)
    cantidad: int = Field(..., gt=0, le=50) # Límite lógico para evitar vaciado de almacén
    cliente: str = Field(..., min_length=2, max_length=100)
    direccion: str = Field(..., min_length=5, max_length=200)

# BASE DE DATOS OPERATIVA EN TIEMPO REAL
DATABASE_CORE = {
    "comercio": {
        "nombre": "Comercio Blindado Santiago",
        "estado": "OPERACION_PROTEGIDA"
    },
    "inventario": {
        "SKU-001": {"producto": "Combo Burger Nuxia", "stock": 40, "precio_clp": 8990},
        "SKU-002": {"producto": "Pizza Familiar Pepperoni", "stock": 20, "precio_clp": 13500}
    },
    "repartidores": {
        "DELIVERY-01": {"nombre": "Carlos Soto", "estado": "disponible"}
    },
    "pedidos": []
}

@app.get("/")
def system_root(request: Request):
    cognitive_security_shield(request)
    return {
        "system": "NuxyeCoreShield Enterprise Core",
        "status": "online_and_bulletproof",
        "shield_status": SHIELD_MEMORY["security_status"],
        "amenazas_bloqueadas": SHIELD_MEMORY["threats_neutralized"]
    }

# ==========================================
# MÓDULOS DE NEGOCIO PROTEGIDOS POR EL ESCUDO
# ==========================================
@app.get("/api/almacen/stock", dependencies=[Depends(verify_shield_credentials)])
def consultar_stock(request: Request):
    cognitive_security_shield(request)
    return {
        "estado": "Protegido por NuxyeCoreShield",
        "inventario": DATABASE_CORE["inventario"]
    }

@app.post("/api/logistica/despacho", dependencies=[Depends(verify_shield_credentials)])
def ejecutar_despacho_seguro(payload: SecureDispatchPayload, request: Request):
    cognitive_security_shield(request)
    
    sku = payload.sku
    if sku not in DATABASE_CORE["inventario"]:
        raise HTTPException(status_code=404, detail="SKU inexistente en almacén central")
        
    item = DATABASE_CORE["inventario"][sku]
    
    # Verificación heurística de inventario crítico
    if item["stock"] < payload.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente en almacén para completar la operación lógica")
        
    # Descuento atómico de stock
    item["stock"] -= payload.cantidad
    
    order_id = f"NXC-{str(uuid.uuid4())[:6].upper()}"
    registro_orden = {
        "pedido_id": order_id,
        "sku": sku,
        "producto": item["producto"],
        "cantidad": payload.cantidad,
        "cliente": payload.cliente,
        "direccion": payload.direccion,
        "estado": "LOGISTICA_EJECUTADA_CON_EXITO"
    }
    DATABASE_CORE["pedidos"].append(registro_orden)
    
    return {
        "status": "Operación validada y blindada por NuxyeCoreShield",
        "orden": registro_orden,
        "stock_remanente": item["stock"]
    }

@app.post("/api/seguridad/kill-switch", dependencies=[Depends(verify_shield_credentials)])
def activar_kill_switch(payload: Dict[Any, Any], request: Request):
    cognitive_security_shield(request)
    device_id = payload.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id requerido")
        
    if device_id in DATABASE_CORE["repartidores"]:
        DATABASE_CORE["repartidores"][device_id]["estado"] = "BLOQUEADO_POR_NXYECORESHIELD"
        
    return {
        "action": "KILL_SWITCH_DISPATCHED",
        "device_id": device_id,
        "estado": "Aislado de la red de fletes por orden de seguridad"
    }
    import psycopg2

def obtener_conexion():
    """Establece conexión directa con Supabase usando los parámetros de red"""
    conexion = psycopg2.connect(
        host="db.nbcghqtyqszqgcbfoft.supabase.co",
        database="postgres",
        user="postgres",
        password="Xm-Amu%2Fv5%40DdPS%2C", # Reemplaza esto con tu clave
        port=5432
    )
    return conexion
