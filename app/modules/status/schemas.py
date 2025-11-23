"""
Schemas de Configuración de Estado, Sub-Estados y Transiciones
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# ConfigEstado - Base Schemas
# ============================================

class ConfigEstadoBase(BaseModel):
    """Schema base de configuración de estado"""
    nombre: str = Field(min_length=1, max_length=100, description="Nombre del estado")
    color: str = Field(min_length=1, max_length=50, description="Color del estado")
    posicion_orden: int = Field(ge=0, description="Posición en el orden")


# ============================================
# ConfigEstado - Request Schemas
# ============================================

class ConfigEstadoCrear(ConfigEstadoBase):
    """Schema para crear configuración de estado"""
    pass


class ConfigEstadoActualizar(BaseModel):
    """Schema para actualizar configuración de estado"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, min_length=1, max_length=50)
    posicion_orden: Optional[int] = Field(None, ge=0)


# ============================================
# ConfigEstado - Response Schemas
# ============================================

class ConfigEstadoRespuesta(ConfigEstadoBase):
    """Schema de respuesta de configuración de estado"""
    id: UUID = Field(description="ID único de la configuración")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SubEstado - Base Schemas
# ============================================

class SubEstadoBase(BaseModel):
    """Schema base de sub-estado"""
    nombre: str = Field(min_length=1, max_length=100, description="Nombre del sub-estado")
    descripcion: Optional[str] = Field(None, description="Descripción del sub-estado")
    posicion_orden: int = Field(ge=0, description="Posición en el orden")


# ============================================
# SubEstado - Request Schemas
# ============================================

class SubEstadoCrear(SubEstadoBase):
    """Schema para crear sub-estado"""
    estado_id: UUID = Field(description="ID de la configuración de estado padre")


class SubEstadoActualizar(BaseModel):
    """Schema para actualizar sub-estado"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    posicion_orden: Optional[int] = Field(None, ge=0)


# ============================================
# SubEstado - Response Schemas
# ============================================

class SubEstadoRespuesta(SubEstadoBase):
    """Schema de respuesta de sub-estado"""
    id: UUID = Field(description="ID único del sub-estado")
    estado_id: UUID = Field(description="ID de la configuración de estado padre")
    creado_en: datetime = Field(description="Fecha de creación")
    
    model_config = ConfigDict(from_attributes=True)


class SubEstadoConEstado(SubEstadoRespuesta):
    """Schema de sub-estado con información del estado padre"""
    estado_nombre: Optional[str] = Field(None, description="Nombre del estado padre")
    estado_color: Optional[str] = Field(None, description="Color del estado padre")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# TransicionEstado - Base Schemas
# ============================================

class TransicionEstadoBase(BaseModel):
    """Schema base de transición de estado"""
    desde_estado: UUID = Field(description="ID del estado origen")
    hacia_estado: UUID = Field(description="ID del estado destino")
    roles_requeridos: List[str] = Field(description="Roles que pueden ejecutar esta transición")
    requiere_confirmacion: bool = Field(default=False, description="Si requiere confirmación del usuario")
    mensaje: Optional[str] = Field(None, description="Mensaje a mostrar al usuario")


# ============================================
# TransicionEstado - Request Schemas
# ============================================

class TransicionEstadoCrear(TransicionEstadoBase):
    """Schema para crear transición de estado"""
    pass


class TransicionEstadoActualizar(BaseModel):
    """Schema para actualizar transición de estado"""
    roles_requeridos: Optional[List[str]] = None
    requiere_confirmacion: Optional[bool] = None
    mensaje: Optional[str] = None


# ============================================
# TransicionEstado - Response Schemas
# ============================================

class TransicionEstadoRespuesta(TransicionEstadoBase):
    """Schema de respuesta de transición de estado"""
    id: UUID = Field(description="ID único de la transición")
    creado_en: datetime = Field(description="Fecha de creación")
    
    model_config = ConfigDict(from_attributes=True)


class TransicionEstadoDetalle(TransicionEstadoRespuesta):
    """Schema detallado de transición con nombres de estados"""
    desde_estado_nombre: Optional[str] = Field(None, description="Nombre del estado origen")
    hacia_estado_nombre: Optional[str] = Field(None, description="Nombre del estado destino")
    desde_estado_color: Optional[str] = Field(None, description="Color del estado origen")
    hacia_estado_color: Optional[str] = Field(None, description="Color del estado destino")
    
    model_config = ConfigDict(from_attributes=True)
