"""
Schemas de Reclamo (Claim), Eventos de Auditoría, Comentarios y Adjuntos
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, AliasChoices

from app.modules.claims.models import ClaimPriority
from app.modules.users.schemas import UsuarioSimple
from app.modules.status.schemas import ConfigEstadoRespuesta, SubEstadoRespuesta


# ============================================
# Reclamo - Base Schemas
# ============================================

class ReclamoBase(BaseModel):
    """Schema base de reclamo"""
    asunto: str = Field(min_length=1, max_length=500, description="Asunto del reclamo")
    nombre_cliente: str = Field(min_length=1, max_length=255, description="Nombre del cliente")
    info_contacto: str = Field(min_length=1, max_length=255, description="Información de contacto")
    descripcion: str = Field(min_length=1, description="Descripción detallada")
    estado_id: Union[UUID, str] = Field(description="ID del estado o nombre del estado (ej: 'Nuevo')")
    prioridad: Optional[ClaimPriority] = Field(ClaimPriority.MEDIUM, description="Prioridad")


# ============================================
# Reclamo - Request Schemas
# ============================================

class ReclamoCrear(ReclamoBase):
    """Schema para crear reclamo"""
    categoria: Optional[str] = Field(None, max_length=100, description="Categoría del reclamo")
    email_cliente: Optional[str] = Field(None, max_length=255, description="Email del cliente")
    telefono_cliente: Optional[str] = Field(None, max_length=50, description="Teléfono del cliente")
    proyecto_id: Optional[UUID] = Field(None, description="ID del proyecto asociado")
    
    model_config = ConfigDict(extra='ignore')  # Ignorar campos adicionales como cliente_id


class ReclamoActualizar(BaseModel):
    """Schema para actualizar reclamo (campos opcionales)"""
    asunto: Optional[str] = Field(None, min_length=1, max_length=500)
    nombre_cliente: Optional[str] = Field(None, min_length=1, max_length=255)
    info_contacto: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, min_length=1)
    estado_id: Optional[Union[UUID, str]] = Field(None, description="ID del estado o nombre del estado")
    sub_estado_id: Optional[Union[UUID, str]] = Field(
        None, 
        validation_alias=AliasChoices('sub_estado_id', 'sub_estado'),
        description="ID del sub-estado o nombre del sub-estado"
    )
    prioridad: Optional[ClaimPriority] = None
    categoria: Optional[str] = Field(None, max_length=100)
    email_cliente: Optional[str] = Field(None, max_length=255)
    telefono_cliente: Optional[str] = Field(None, max_length=50)
    proyecto_id: Optional[UUID] = Field(None, description="ID del proyecto asociado")


class ReclamoAsignar(BaseModel):
    """Schema para asignar reclamo a un agente"""
    agente_id: Optional[UUID] = Field(None, description="ID del agente (null para desasignar)")


class ReclamoCambiarEstado(BaseModel):
    """Schema para cambiar el estado de un reclamo"""
    nuevo_estado: UUID = Field(description="ID del nuevo estado")
    resumen_resolucion: Optional[str] = Field(None, description="Resumen de resolución (requerido para estado 'resuelto')")


class ReclamoCambiarSubEstado(BaseModel):
    """Schema para cambiar el sub-estado de un reclamo"""
    nuevo_sub_estado: UUID = Field(description="ID del nuevo sub-estado")


# ============================================
# Reclamo - Response Schemas
# ============================================

class ReclamoRespuesta(ReclamoBase):
    """Schema de respuesta básico de reclamo"""
    id: UUID = Field(description="ID único del reclamo")
    asignado_a: Optional[UUID] = Field(None, description="ID del agente asignado")
    sub_estado_id: Optional[UUID] = Field(None, description="ID del sub-estado actual")
    categoria: Optional[str] = Field(None, description="Categoría del reclamo")
    email_cliente: Optional[str] = Field(None, description="Email del cliente")
    telefono_cliente: Optional[str] = Field(None, description="Teléfono del cliente")
    proyecto_id: Optional[UUID] = Field(None, description="ID del proyecto asociado")
    resumen_resolucion: Optional[str] = Field(None, description="Resumen de resolución")
    bloqueado: bool = Field(default=False, description="Si está bloqueado para edición")
    resuelto_en: Optional[datetime] = Field(None, description="Fecha de resolución")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    # Objetos anidados (cargados via relationship)
    estado_config: Optional[ConfigEstadoRespuesta] = Field(None, description="Configuración del estado actual")
    sub_estado_config: Optional[SubEstadoRespuesta] = Field(None, description="Configuración del sub-estado actual")
    agente_asignado: Optional[UsuarioSimple] = Field(None, description="Agente asignado al reclamo")
    
    model_config = ConfigDict(from_attributes=True)


class ReclamoItemLista(ReclamoRespuesta):
    """Schema de reclamo para listado (con agente asignado)"""
    agente_asignado: Optional[UsuarioSimple] = Field(None, description="Agente asignado")
    cantidad_comentarios: int = Field(default=0, description="Cantidad de comentarios")
    cantidad_adjuntos: int = Field(default=0, description="Cantidad de adjuntos")
    
    model_config = ConfigDict(from_attributes=True)


class ReclamoDetalle(ReclamoRespuesta):
    """Schema de reclamo detallado (con relaciones)"""
    agente_asignado: Optional[UsuarioSimple] = Field(None, description="Agente asignado")
    comentarios: List["ComentarioReclamoRespuesta"] = Field(default_factory=list, description="Comentarios del reclamo")
    adjuntos: List["AdjuntoReclamoRespuesta"] = Field(default_factory=list, description="Archivos adjuntos")
    eventos_recientes: List["EventoAuditoriaRespuesta"] = Field(default_factory=list, description="Últimos eventos de auditoría")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# EventoAuditoria - Base Schemas
# ============================================

class EventoAuditoriaBase(BaseModel):
    """Schema base de evento de auditoría"""
    tipo_evento: str = Field(min_length=1, max_length=50, description="Tipo de evento (created, status_changed, assigned, etc.)")
    nombre_usuario: str = Field(min_length=1, max_length=255, description="Nombre del usuario que ejecutó la acción")
    area_usuario: Optional[str] = Field(None, max_length=100, description="Área del usuario")
    cambios: Optional[Dict[str, Any]] = Field(None, description="Detalles de los cambios realizados")
    descripcion: Optional[str] = Field(None, description="Descripción del evento")


# ============================================
# EventoAuditoria - Response Schemas
# ============================================

class EventoAuditoriaRespuesta(EventoAuditoriaBase):
    """Schema de respuesta de evento de auditoría"""
    id: UUID = Field(description="ID único del evento")
    reclamo_id: UUID = Field(description="ID del reclamo asociado")
    usuario_id: Optional[UUID] = Field(None, description="ID del usuario (si aplica)")
    creado_en: datetime = Field(description="Fecha del evento")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# ComentarioReclamo - Base Schemas
# ============================================

class ComentarioReclamoBase(BaseModel):
    """Schema base de comentario en reclamo"""
    contenido: str = Field(min_length=1, description="Contenido del comentario")
    es_interno: bool = Field(default=False, description="Si es visible solo para el equipo")


# ============================================
# ComentarioReclamo - Request Schemas
# ============================================

class ComentarioReclamoCrear(ComentarioReclamoBase):
    """Schema para crear comentario"""
    pass


class ComentarioReclamoActualizar(BaseModel):
    """Schema para actualizar comentario"""
    contenido: str = Field(min_length=1, description="Nuevo contenido del comentario")


# ============================================
# ComentarioReclamo - Response Schemas
# ============================================

class ComentarioReclamoRespuesta(ComentarioReclamoBase):
    """Schema de respuesta de comentario"""
    id: UUID = Field(description="ID único del comentario")
    reclamo_id: UUID = Field(description="ID del reclamo asociado")
    usuario_id: UUID = Field(description="ID del usuario que creó el comentario")
    usuario: Optional[UsuarioSimple] = Field(None, description="Información del usuario")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# AdjuntoReclamo - Base Schemas
# ============================================

class AdjuntoReclamoBase(BaseModel):
    """Schema base de archivo adjunto"""
    nombre_archivo: str = Field(min_length=1, max_length=255, description="Nombre del archivo")
    url_archivo: str = Field(min_length=1, description="URL o path del archivo")
    tipo_archivo: Optional[str] = Field(None, max_length=100, description="MIME type del archivo")
    tamano_archivo: Optional[int] = Field(None, ge=0, description="Tamaño en bytes")


# ============================================
# AdjuntoReclamo - Request Schemas
# ============================================

class AdjuntoReclamoCrear(BaseModel):
    """Schema para crear adjunto (usado después de upload)"""
    nombre_archivo: str = Field(min_length=1, max_length=255)
    url_archivo: str = Field(min_length=1)
    tipo_archivo: Optional[str] = Field(None, max_length=100)
    tamano_archivo: Optional[int] = Field(None, ge=0)


# ============================================
# AdjuntoReclamo - Response Schemas
# ============================================

class AdjuntoReclamoRespuesta(AdjuntoReclamoBase):
    """Schema de respuesta de adjunto"""
    id: UUID = Field(description="ID único del adjunto")
    reclamo_id: UUID = Field(description="ID del reclamo asociado")
    subido_por: UUID = Field(description="ID del usuario que subió el archivo")
    usuario: Optional[UsuarioSimple] = Field(None, description="Información del usuario")
    creado_en: datetime = Field(description="Fecha de subida")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Forward References Update
# ============================================

# Actualizar forward references para que las relaciones funcionen correctamente
ReclamoDetalle.model_rebuild()
