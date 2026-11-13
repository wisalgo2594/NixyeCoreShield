from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.core.database import get_db
from app.core.security import obtener_usuario_actual
from app.schemas.dtos import InventarioItem
from app.models.entities import InventarioModel

router = APIRouter(prefix="/inventario", tags=["Logística e Inventario Atómico"])

@router.post("/sincronizar")
async def sincronizar_inventario(
    item: InventarioItem,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(obtener_usuario_actual)
):
    try:
        stmt = insert(InventarioModel).values(
            comercio_id=item.comercio_id,
            sku=item.sku,
            producto=item.producto,
            stock=item.stock,
            precio_clp=item.precio_clp
        )
        
        stmt = stmt.on_conflict_do_update(
            constraint='uq_comercio_sku_enterprise',
            set_dict={
                "producto": stmt.excluded.producto,
                "stock": stmt.excluded.stock,
                "precio_clp": stmt.excluded.precio_clp
            }
        )
        
        await db.execute(stmt)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"NixyeCore: Inventario SKU '{item.sku}' sincronizado sin duplicados.",
            "operado_por": current_user
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo crítico en sincronización atómica: {str(e)}"
        )