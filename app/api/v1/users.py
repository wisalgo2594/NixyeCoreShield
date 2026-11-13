from fastapi import APIRouter
from app.api.deps import CurrentUser, CurrentSuperuser
from app.models.entities import User

router = APIRouter()

@router.get("/me", summary="Obtener perfil del usuario autenticado")
async def read_users_me(current_user: CurrentUser):
    """
    Cualquier usuario autenticado puede ver su propio perfil.
    """
    return {
        "status": "success",
        "email": current_user.email,
        "is_superuser": current_user.is_superuser
    }

@router.get("/admin/dashboard", summary="Panel exclusivo para Superusuarios")
async def admin_dashboard(current_superuser: CurrentSuperuser):
    """
    Solo pasa el superusuario. Si es un usuario normal, bota un 403.
    """
    return {
        "status": "success",
        "message": f"Bienvenido al núcleo de administración, {current_superuser.email}"
    }