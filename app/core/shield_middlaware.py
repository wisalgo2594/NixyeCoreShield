import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("NixyeCore.Shield")

class NixyeCoreShieldMiddleware(BaseHTTPMiddleware):
    """
    Middleware de seguridad y auditoría de nivel empresarial para NixyeCore.
    Añade trazabilidad por Request ID, métricas de rendimiento y cabeceras de seguridad.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Generar un ID único por petición para trazabilidad estricta
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        
        try:
            # 2. Procesar la solicitud entrante
            response = await call_next(request)
            
            # 3. Calcular tiempo de procesamiento en ms
            process_time_ms = (time.time() - start_time) * 1000

            # 4. Inyectar cabeceras corporativas y de seguridad defensiva (OWASP)
            response.headers["X-Nixye-Shield"] = "Active-Protected-Enterprise"
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # 5. Registrar tráfico exitoso sensible (opcional o depuración)
            if process_time_ms > 1000:  # Alerta si una petición tarda más de 1 segundo
                logger.warning(f"[SLOW REQUEST] Ruta: {request.url.path} tardó {process_time_ms:.2f}ms [ID: {request_id}]")

            return response

        except Exception as exc:
            # 6. Blindaje ante fallos críticos de propagación
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(f"[SHIELD CRITICAL ERROR] Ruta: {request.url.path} | Error: {str(exc)} [ID: {request_id}]")
            raise exc