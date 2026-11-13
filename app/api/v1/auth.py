from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.security import create_access_token

router = APIRouter()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse, summary="Autenticación y generación de JWT")
async def login_access_token(form_data: UserLogin):
    # Credenciales de validación enterprise (puedes conectarlo a la base de datos más adelante)
    if form_data.email == "admin@nixye.com" and form_data.password == "admin123":
        access_token = create_access_token(data={"sub": form_data.email, "role": "superuser"})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas o usuario no autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )