from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import obtener_usuario_actual
from app.models.entities import AuditoriaSeguridadModel

router = APIRouter(prefix="/shield", tags=["NixyeCoreShield & Auditoría"])

@router.get("/auditoria/amenazas")
async def consultar_amenazas(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(obtener_usuario_actual)
):
    try:
        result = await db.execute(
            select(AuditoriaSeguridadModel)
            .order_by(AuditoriaSeguridadModel.fecha.desc())
            .limit(50)
        )
        amenazas = result.scalars().all()
        
        return {
            "status": "success",
            "shield_status": "Activo y Blindado",
            "registros_intrusiones": [
                {
                    "id": a.id,
                    "endpoint_afectado": a.endpoint,
                    "motivo_bloqueo": a.motivo,
                    "ip_origen": a.ip_origen,
                    "marca_temporal": str(a.fecha)
                }
                for a in amenazas
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el buffer de auditoría: {str(e)}"
        )