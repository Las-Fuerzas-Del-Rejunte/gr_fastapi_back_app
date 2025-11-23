"""
Schemas de Usuario - Adaptados para MongoDB/Beanie
"""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from bson import ObjectId


# Serializer personalizado para ObjectId
class PyObjectId(str):
    """Clase helper para serializar ObjectId como string"""
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


# ============================================
# Base Schemas
# ============================================

class UsuarioBase(BaseModel):
    """Schema base de usuario"""
    email: EmailStr = Field(description="Email del usuario")
    nombre: str = Field(min_length=1, max_length=255, description="Nombre completo")
    rol: Literal["admin", "manager", "agent", "viewer"] = Field(description="Rol del usuario")
    telefono: Optional[str] = Field(None, max_length=50, description="Teléfono")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")
    posicion: Optional[str] = Field(None, max_length=100, description="Posición")
    area: Optional[str] = Field(None, max_length=100, description="Área")
    avatar_url: Optional[str] = Field(None, description="URL del avatar")
    activo: bool = Field(True, description="Usuario activo")


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
    area: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    rol: Optional[Literal["admin", "manager", "agent", "viewer"]] = None
    activo: Optional[bool] = None


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

class UsuarioRespuesta(BaseModel):
    """Schema de respuesta completo de usuario"""
    id: PyObjectId = Field(alias="_id", description="ID único del usuario")
    email: EmailStr = Field(description="Email del usuario")
    nombre: str = Field(description="Nombre completo")
    rol: Literal["admin", "manager", "agent", "viewer"] = Field(description="Rol del usuario")
    telefono: Optional[str] = Field(None, description="Teléfono")
    departamento: Optional[str] = Field(None, description="Departamento")
    posicion: Optional[str] = Field(None, description="Posición")
    area: Optional[str] = Field(None, description="Área")
    avatar_url: Optional[str] = Field(None, description="URL del avatar")
    activo: bool = Field(description="Usuario activo")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class UsuarioSimple(BaseModel):
    """Schema simplificado de usuario (para relaciones)"""
    id: PyObjectId = Field(alias="_id")
    nombre: str
    email: EmailStr
    posicion: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
