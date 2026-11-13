from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import logging

# Importaciones de la aplicación
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.items import router as items_router  # Importación de items
from app.core.config import settings
from app.core.database import engine
from app.models.entities import Base

# Configurar un logger básico para producción
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de ciclo de vida.
    Al arrancar: Crea las tablas en la base de datos si no existen.
    Al apagar: Cierra las conexiones del pool de forma limpia.
    """
    logger.info("Iniciando aplicación y conectando a la base de datos...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas verificadas/creadas exitosamente.")
    except Exception as e:
        logger.error(f"Error conectando a la base de datos al arrancar: {e}")
    
    yield
    
    logger.info("Apagando aplicación y cerrando conexiones...")
    await engine.dispose()
    logger.info("Conexiones cerradas.")


# 1. Configuración del Rate Limiter (SlowAPI)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
)

# 2. Creación de la App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend Empresarial con FastAPI, SQLAlchemy Async y Neon",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Configuración de Middlewares
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Manejo Global de Excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no controlado en la ruta {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno en el servidor. Contacte al administrador."},
    )

# 5. Registro de Rutas (Routers) - ¡Solo una vez!
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(items_router, prefix="/api/v1/items", tags=["Items"])

# 6. Rutas Básicas (Ping / Health)
@app.get("/", tags=["Sistema"])
@limiter.exempt
async def root():
    return {
        "ecosistema": "NixyeCore & NixyeCoreShield Enterprise",
        "status": "online",
        "documentacion": "/docs",
    }

@app.get("/health", tags=["Sistema"])
@limiter.exempt
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}