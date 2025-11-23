"""
Schemas de Usuario (Pydantic)
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.modules.users.models import UserRole


# ============================================
# Base Schemas
# ============================================

class UsuarioBase(BaseModel):
    """Schema base de usuario"""
    email: EmailStr = Field(description="Email del usuario")
    nombre: str = Field(min_length=1, max_length=255, description="Nombre completo")
    rol: UserRole = Field(description="Rol del usuario")
    telefono: Optional[str] = Field(None, max_length=50, description="Teléfono")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")
    posicion: Optional[str] = Field(None, max_length=100, description="Posición")


# ============================================
# Request Schemas
# ============================================

class UsuarioCrear(UsuarioBase):
    """Schema para crear usuario"""
    contrasena: str = Field(
        min_length=8,
        max_length=100,
        description="Contraseña (mínimo 8 caracteres)"
    )


class UsuarioActualizar(BaseModel):
    """Schema para actualizar usuario (campos opcionales)"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    departamento: Optional[str] = Field(None, max_length=100)
    posicion: Optional[str] = Field(None, max_length=100)
    rol: Optional[UserRole] = None


class UsuarioCambiarContrasena(BaseModel):
    """Schema para cambiar contraseña"""
    contrasena_actual: str = Field(description="Contraseña actual")
    contrasena_nueva: str = Field(
        min_length=8,
        max_length=100,
        description="Nueva contraseña"
    )


# ============================================
# Response Schemas
# ============================================

class UsuarioRespuesta(UsuarioBase):
    """Schema de respuesta completo de usuario"""
    id: UUID = Field(description="ID único del usuario")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(from_attributes=True)


class UsuarioSimple(BaseModel):
    """Schema simplificado de usuario (para relaciones)"""
    id: UUID
    nombre: str
    email: EmailStr
    posicion: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
