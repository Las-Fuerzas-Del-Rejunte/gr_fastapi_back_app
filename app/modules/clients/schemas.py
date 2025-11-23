"""
Schemas de Clientes y Proyectos
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


# ============================================
# TipoProyecto Schemas
# ============================================

class TipoProyectoBase(BaseModel):
    """Schema base de Tipo de Proyecto"""
    descripcion: str = Field(max_length=200, description="Descripción del tipo de proyecto")
    activo: bool = Field(default=True, description="Estado activo/inactivo")


class TipoProyectoCrear(TipoProyectoBase):
    """Schema para crear Tipo de Proyecto"""
    pass


class TipoProyectoActualizar(BaseModel):
    """Schema para actualizar Tipo de Proyecto"""
    descripcion: Optional[str] = Field(None, max_length=200)
    activo: Optional[bool] = None


class TipoProyectoRespuesta(TipoProyectoBase):
    """Schema de respuesta de Tipo de Proyecto"""
    id: uuid.UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = {"from_attributes": True}


# ============================================
# Cliente Schemas
# ============================================

class ClienteBase(BaseModel):
    """Schema base de Cliente"""
    nombre: str = Field(max_length=100, description="Nombre del cliente")
    apellido: str = Field(max_length=100, description="Apellido del cliente")
    telefono: Optional[str] = Field(None, max_length=50, description="Teléfono de contacto")
    correo: EmailStr = Field(description="Correo electrónico")
    empresa: Optional[str] = Field(None, max_length=200, description="Empresa del cliente")
    activo: bool = Field(default=True, description="Estado activo/inactivo")


class ClienteCrear(ClienteBase):
    """Schema para crear Cliente"""
    pass


class ClienteActualizar(BaseModel):
    """Schema para actualizar Cliente"""
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=50)
    correo: Optional[EmailStr] = None
    empresa: Optional[str] = Field(None, max_length=200)
    activo: Optional[bool] = None


class ClienteRespuesta(ClienteBase):
    """Schema de respuesta de Cliente"""
    id: uuid.UUID
    nombre_completo: str
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = {"from_attributes": True}


# ============================================
# Proyecto Schemas
# ============================================

class ProyectoBase(BaseModel):
    """Schema base de Proyecto"""
    nombre: str = Field(max_length=200, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción del proyecto")
    cliente_id: uuid.UUID = Field(description="ID del cliente")
    tipo_proyecto_id: uuid.UUID = Field(description="ID del tipo de proyecto")
    activo: bool = Field(default=True, description="Estado activo/inactivo")


class ProyectoCrear(ProyectoBase):
    """Schema para crear Proyecto"""
    pass


class ProyectoActualizar(BaseModel):
    """Schema para actualizar Proyecto"""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    cliente_id: Optional[uuid.UUID] = None
    tipo_proyecto_id: Optional[uuid.UUID] = None
    activo: Optional[bool] = None


class ProyectoRespuesta(ProyectoBase):
    """Schema de respuesta de Proyecto"""
    id: uuid.UUID
    cliente: ClienteRespuesta
    tipo_proyecto: TipoProyectoRespuesta
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = {"from_attributes": True}


class ProyectoSimple(BaseModel):
    """Schema simplificado de Proyecto para listados"""
    id: uuid.UUID
    nombre: str
    cliente_id: uuid.UUID
    tipo_proyecto_id: uuid.UUID
    activo: bool
    
    model_config = {"from_attributes": True}
