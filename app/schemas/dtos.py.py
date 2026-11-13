from pydantic import BaseModel, Field

class TokenSchema(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class InventarioItem(BaseModel):
    comercio_id: str = Field(..., min_length=1, description="ID único del comercio")
    sku: str = Field(..., min_length=1, description="SKU único del producto")
    producto: str = Field(..., min_length=1, description="Nombre descriptivo")
    stock: int = Field(..., ge=0, description="Stock disponible (>= 0)")
    precio_clp: float = Field(..., ge=0, description="Precio en CLP (>= 0)")