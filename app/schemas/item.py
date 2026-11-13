from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Optional, Annotated, Self

from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field, 
    StringConstraints, 
    field_validator, 
    model_validator
)

# =============================================================================
# SANITIZACIÓN DE ÉLITE
# Neutraliza vectores de inyección Unicode (Bidi spoofing, control chars, null bytes).
# =============================================================================
_CTRL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u0080-\u009f\u2028\u2029]")
_BIDI_CONTROL_RE = re.compile(r"[\u202a-\u202e\u2066-\u2069]")

def _sanitize_text(value: str) -> str:
    value = _BIDI_CONTROL_RE.sub("", value)
    value = _CTRL_CHAR_RE.sub("", value)
    return re.sub(r"\s+", " ", value).strip()

ItemName = Annotated[str, StringConstraints(min_length=1, max_length=255)]

# =============================================================================
# MODELOS DE CREACIÓN Y RESPUESTA (Estrictos)
# =============================================================================
class ItemBase(BaseModel):
    # `extra="forbid"` rechaza campos no declarados (Zero-Trust)
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: ItemName
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(gt=0, description="Price must be greater than 0")
    is_active: bool = True

    @field_validator("name", mode="after")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        cleaned = _sanitize_text(v)
        if not cleaned:
            raise ValueError("name must contain at least one visible glyph")
        return cleaned

    @field_validator("price", mode="after")
    @classmethod
    def _validate_price(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price must be finite (NaN/Inf rejected)")
        return v

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

# =============================================================================
# MODELO DE ACTUALIZACIÓN (Nivel Dios)
# Aquí está la magia para derrotar a Hypothesis.
# =============================================================================
class ItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # Usamos Union implícita: si envían null, Pydantic lo deja pasar como None
    # PERO usaremos un model_validator para interceptar y rechazar nulos explícitos.
    name: Optional[ItemName] = None
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None

    @field_validator("name", mode="after")
    @classmethod
    def _clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = _sanitize_text(v)
        if not cleaned:
            raise ValueError("name cannot be empty after sanitization")
        return cleaned

    @field_validator("price", mode="after")
    @classmethod
    def _validate_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not math.isfinite(v):
            raise ValueError("price must be finite")
        return v

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> Self:
        """
        INVARIANTE DE SEGURIDAD:
        Si un cliente envía {"name": null} o {"price": null} intencionalmente,
        Pydantic lanzará un ValueError limpio (HTTP 422) en lugar de dejar que
        el servicio intente un UPDATE corrupto en la base de datos.
        """
        fields_set = self.model_fields_set
        
        if "name" in fields_set and self.name is None:
            raise ValueError("field 'name' cannot be explicitly set to null")
            
        if "price" in fields_set and self.price is None:
            raise ValueError("field 'price' cannot be explicitly set to null")
            
        return self

# =============================================================================
# PAGINACIÓN BLINDADA
# =============================================================================
class PaginatedItems(BaseModel):
    total: Annotated[int, Field(ge=0)]
    page: Annotated[int, Field(ge=1)]
    size: Annotated[int, Field(ge=1, le=100)]
    items: list[ItemResponse]

    @model_validator(mode="after")
    def _bounds_consistent(self) -> Self:
        if len(self.items) > self.size:
            raise ValueError("length of items exceeds declared page size")
        return self