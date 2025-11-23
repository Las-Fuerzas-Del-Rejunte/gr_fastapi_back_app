"""
Schemas Pydantic para Claims/Reclamos - MongoDB Version
Serializadores para las APIs REST
"""
from typing import Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from bson import ObjectId


# ============================================
# PyObjectId Serializer
# ============================================

class PyObjectId(str):
    """Custom type for serializing MongoDB ObjectId"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            try:
                return str(ObjectId(v))
            except Exception:
                raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId")


# ============================================
# Embedded Documents Schemas
# ============================================

class SubEstadoEmbedRespuesta(BaseModel):
    """Schema para sub-estado embebido en reclamo"""
    nombre: str
    descripcion: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class ConfiguracionEstadoEmbedRespuesta(BaseModel):
    """Schema para configuración de estado embebido en reclamo"""
    nombre: str
    color: str
    descripcion: Optional[str] = None
    orden: int
    sub_estado: Optional[SubEstadoEmbedRespuesta] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class TransicionEstadoRespuesta(BaseModel):
    """Schema para transición de estado"""
    id: PyObjectId = Field(alias="_id")
    fecha_transicion: datetime
    estado_anterior: Optional[ConfiguracionEstadoEmbedRespuesta] = None
    estado_nuevo: ConfiguracionEstadoEmbedRespuesta
    usuario_id: Optional[PyObjectId] = None
    comentario: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


# ============================================
# Reclamo Schemas
# ============================================

class ReclamoCrear(BaseModel):
    """Schema para crear un reclamo"""
    asunto: str
    descripcion: str
    nombre_cliente: str = Field(description="Nombre del cliente")
    info_contacto: str = Field(description="Email o teléfono de contacto")
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    categoria: Optional[str] = None
    proyecto_id: Optional[str] = None  # Acepta string de ObjectId o None
    prioridad: Literal["low", "medium", "high", "critical"] = "medium"
    estado_id: Optional[str] = None  # Acepta string de ObjectId o None
    
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')


class ReclamoActualizar(BaseModel):
    """Schema para actualizar un reclamo"""
    asunto: Optional[str] = None
    descripcion: Optional[str] = None
    nombre_cliente: Optional[str] = None
    info_contacto: Optional[str] = None
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    categoria: Optional[str] = None
    prioridad: Optional[Literal["low", "medium", "high", "critical"]] = None
    estado_id: Optional[str] = None  # Acepta string de ObjectId
    sub_estado_id: Optional[str] = None  # Acepta string de ObjectId
    asignado_a: Optional[str] = None  # Acepta string de ObjectId
    proyecto_id: Optional[str] = None  # Acepta string de ObjectId
    resumen_resolucion: Optional[str] = None
    bloqueado: Optional[bool] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')


class ReclamoAsignar(BaseModel):
    """Schema para asignar un reclamo a un agente"""
    agente_id: Optional[str] = None  # Acepta string de ObjectId o None para desasignar
    
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='ignore')


class ReclamoItemLista(BaseModel):
    """Schema para un item de reclamo en lista"""
    id: PyObjectId = Field(alias="_id")
    numero_reclamo: str
    asunto: str
    cliente_nombre: str
    prioridad: str
    estado_actual: Optional[ConfiguracionEstadoEmbedRespuesta] = None
    asignado_a_nombre: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    cantidad_comentarios: int = 0
    cantidad_adjuntos: int = 0
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class ReclamoRespuesta(BaseModel):
    """Schema de respuesta para un reclamo"""
    id: PyObjectId = Field(alias="_id")
    numero_reclamo: str
    asunto: str
    descripcion: str
    cliente_id: PyObjectId
    cliente_nombre: str
    prioridad: str
    estado_actual: Optional[ConfiguracionEstadoEmbedRespuesta] = None
    asignado_a_id: Optional[PyObjectId] = None
    asignado_a_nombre: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    activo: bool = True
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class ReclamoDetalle(ReclamoRespuesta):
    """Schema detallado de un reclamo con historial de transiciones"""
    historial_estados: list[TransicionEstadoRespuesta] = []
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


# ============================================
# Comentario Schemas
# ============================================

class ComentarioReclamoCrear(BaseModel):
    """Schema para crear un comentario"""
    contenido: str


class ComentarioReclamoActualizar(BaseModel):
    """Schema para actualizar un comentario"""
    contenido: str


class ComentarioReclamoRespuesta(BaseModel):
    """Schema de respuesta para un comentario"""
    id: PyObjectId = Field(alias="_id")
    reclamo_id: PyObjectId
    usuario_id: PyObjectId
    usuario_nombre: str
    contenido: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    activo: bool = True
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


# ============================================
# Adjunto Schemas
# ============================================

class AdjuntoReclamoCrear(BaseModel):
    """Schema para crear un adjunto"""
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    url_archivo: str  # URL del archivo en almacenamiento


class AdjuntoReclamoRespuesta(BaseModel):
    """Schema de respuesta para un adjunto"""
    id: PyObjectId = Field(alias="_id")
    reclamo_id: PyObjectId
    usuario_id: PyObjectId
    usuario_nombre: str
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    url_archivo: str
    fecha_creacion: datetime
    activo: bool = True
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


# ============================================
# Evento Auditoría Schemas
# ============================================

class EventoAuditoriaRespuesta(BaseModel):
    """Schema de respuesta para eventos de auditoría"""
    id: PyObjectId = Field(alias="_id")
    reclamo_id: PyObjectId
    usuario_id: Optional[PyObjectId] = None
    usuario_nombre: Optional[str] = None
    tipo_evento: str
    descripcion: str
    detalles: Optional[dict[str, Any]] = None
    fecha_evento: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
