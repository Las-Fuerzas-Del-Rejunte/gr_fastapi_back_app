"""
Modelo MongoDB para Reclamos usando Beanie ODM
Este es el modelo más complejo con documentos embebidos
"""
from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, Literal, List, Annotated, Union, Any
from bson import ObjectId
import json


# ========================================
# Subdocumentos Embebidos
# ========================================

class ComentarioEmbebido(BaseModel):
    """Comentario embebido dentro del reclamo"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    usuario_id: ObjectId
    usuario_nombre: str  # Desnormalizado para performance
    contenido: str
    es_interno: bool = False
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class NotaEmbebida(BaseModel):
    """Nota embebida dentro del reclamo"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    contenido: str
    autor: str
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class AdjuntoEmbebido(BaseModel):
    """Adjunto embebido dentro del reclamo"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    subido_por: ObjectId
    subido_por_nombre: str  # Desnormalizado
    nombre_archivo: str
    url_archivo: str
    tipo_archivo: Optional[str] = None
    tamano_archivo: Optional[int] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class EventoAuditoriaEmbebido(BaseModel):
    """Evento de auditoría embebido dentro del reclamo"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    tipo_evento: str
    usuario_id: Optional[ObjectId] = None
    nombre_usuario: str
    area_usuario: Optional[str] = None
    cambios: Optional[Any] = None  # JSON flexible - puede ser dict o string serializado
    descripcion: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator(mode='before')
    @classmethod
    def parse_json_fields(cls, data):
        """Convierte campos JSON string a dict si es necesario"""
        if isinstance(data, dict) and 'cambios' in data:
            cambios = data['cambios']
            if isinstance(cambios, str):
                try:
                    data['cambios'] = json.loads(cambios)
                except json.JSONDecodeError:
                    data['cambios'] = None
        return data


# ========================================
# Documento Principal: Reclamo
# ========================================

class Reclamo(Document):
    """
    Modelo principal de Reclamo con documentos embebidos
    Colección: reclamos
    """
    
    # Información básica del reclamo
    asunto: str
    nombre_cliente: str
    info_contacto: str
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    descripcion: str
    
    # Clasificación y estado
    estado_id: ObjectId  # Referencia a ConfiguracionEstado
    sub_estado_id: Optional[ObjectId] = None  # Referencia a SubEstado
    prioridad: Literal["low", "medium", "high", "critical"] = "medium"
    categoria: Optional[str] = None
    bloqueado: bool = False
    
    # Relaciones (referencias)
    proyecto_id: Optional[ObjectId] = None  # Referencia a Proyecto
    creado_por: Optional[ObjectId] = None  # Referencia a Usuario
    asignado_a: Optional[ObjectId] = None  # Referencia a Usuario
    
    # Desnormalización opcional para performance
    asignado_info: Optional[dict] = None  # {nombre, email, area}
    
    # Resolución
    resumen_resolucion: Optional[str] = None
    resuelto_en: Optional[datetime] = None
    
    # Timestamps
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    # ========================================
    # DOCUMENTOS EMBEBIDOS
    # ========================================
    comentarios: List[ComentarioEmbebido] = Field(default_factory=list)
    notas: List[NotaEmbebida] = Field(default_factory=list)
    adjuntos: List[AdjuntoEmbebido] = Field(default_factory=list)
    eventos_auditoria: List[EventoAuditoriaEmbebido] = Field(default_factory=list)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "asunto": "Error en facturación",
                "nombre_cliente": "Pedro López",
                "info_contacto": "pedro@mail.com",
                "email_cliente": "pedro@mail.com",
                "telefono_cliente": "+54911234567",
                "descripcion": "El sistema no genera facturas correctamente",
                "estado_id": "507f1f77bcf86cd799439011",
                "prioridad": "high",
                "categoria": "Técnico",
            }
        }
    )
    
    class Settings:
        """Configuración de Beanie"""
        name = "reclamos"
        
        # Índices optimizados para queries comunes
        indexes = [
            "estado_id",
            "prioridad",
            "creado_por",
            "asignado_a",
            "proyecto_id",
            [("creado_en", -1)],  # Descendente para los más recientes primero
            [("actualizado_en", -1)],
            [("estado_id", 1), ("prioridad", 1)],  # Índice compuesto
            [("asignado_a", 1), ("estado_id", 1)],  # Índice compuesto
            # Índice de texto para búsqueda full-text
            [
                ("asunto", "text"),
                ("descripcion", "text"),
                ("nombre_cliente", "text"),
            ],
        ]
    
    # ========================================
    # Métodos de utilidad para comentarios
    # ========================================
    
    def agregar_comentario(
        self,
        usuario_id: ObjectId,
        usuario_nombre: str,
        contenido: str,
        es_interno: bool = False
    ) -> ComentarioEmbebido:
        """Agrega un comentario al reclamo"""
        comentario = ComentarioEmbebido(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            contenido=contenido,
            es_interno=es_interno,
        )
        self.comentarios.append(comentario)
        self.actualizado_en = datetime.utcnow()
        return comentario
    
    def agregar_nota(self, contenido: str, autor: str) -> NotaEmbebida:
        """Agrega una nota al reclamo"""
        nota = NotaEmbebida(contenido=contenido, autor=autor)
        self.notas.append(nota)
        self.actualizado_en = datetime.utcnow()
        return nota
    
    def agregar_adjunto(
        self,
        subido_por: ObjectId,
        subido_por_nombre: str,
        nombre_archivo: str,
        url_archivo: str,
        tipo_archivo: Optional[str] = None,
        tamano_archivo: Optional[int] = None,
    ) -> AdjuntoEmbebido:
        """Agrega un adjunto al reclamo"""
        adjunto = AdjuntoEmbebido(
            subido_por=subido_por,
            subido_por_nombre=subido_por_nombre,
            nombre_archivo=nombre_archivo,
            url_archivo=url_archivo,
            tipo_archivo=tipo_archivo,
            tamano_archivo=tamano_archivo,
        )
        self.adjuntos.append(adjunto)
        self.actualizado_en = datetime.utcnow()
        return adjunto
    
    def registrar_evento(
        self,
        tipo_evento: str,
        nombre_usuario: str,
        usuario_id: Optional[ObjectId] = None,
        area_usuario: Optional[str] = None,
        cambios: Optional[dict] = None,
        descripcion: Optional[str] = None,
    ) -> EventoAuditoriaEmbebido:
        """Registra un evento de auditoría"""
        evento = EventoAuditoriaEmbebido(
            tipo_evento=tipo_evento,
            usuario_id=usuario_id,
            nombre_usuario=nombre_usuario,
            area_usuario=area_usuario,
            cambios=cambios,
            descripcion=descripcion,
        )
        self.eventos_auditoria.append(evento)
        return evento
    
    # ========================================
    # Métodos de consulta comunes
    # ========================================
    
    @classmethod
    async def find_by_asignado(cls, usuario_id: ObjectId) -> List["Reclamo"]:
        """Encuentra reclamos asignados a un usuario"""
        return await cls.find(cls.asignado_a == usuario_id).to_list()
    
    @classmethod
    async def find_by_estado_and_prioridad(
        cls,
        estado_id: ObjectId,
        prioridad: str
    ) -> List["Reclamo"]:
        """Encuentra reclamos por estado y prioridad"""
        return await cls.find(
            cls.estado_id == estado_id,
            cls.prioridad == prioridad
        ).to_list()
    
    @classmethod
    async def buscar_texto(cls, query: str) -> List["Reclamo"]:
        """Búsqueda full-text en asunto, descripción y cliente"""
        return await cls.find(
            {"$text": {"$search": query}}
        ).to_list()
    
    @classmethod
    async def estadisticas_por_estado(cls) -> List[dict]:
        """Agregación: cuenta reclamos por estado"""
        pipeline = [
            {
                "$group": {
                    "_id": "$estado_id",
                    "count": {"$sum": 1},
                    "prioridad_alta": {
                        "$sum": {
                            "$cond": [{"$eq": ["$prioridad", "high"]}, 1, 0]
                        }
                    }
                }
            },
            {"$sort": {"count": -1}}
        ]
        return await cls.aggregate(pipeline).to_list()


# ========================================
# Modelos de Configuración
# ========================================

class ConfiguracionEstado(Document):
    """Estados configurables del sistema"""
    nombre: str  # Removido índice único
    color: str
    posicion_orden: int
    descripcion: Optional[str] = None
    area: Optional[str] = None
    permisos: Any = Field(default_factory=dict)  # Cambiado a Any para permitir JSON strings
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator(mode='before')
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        """Convierte strings JSON a dicts antes de la validación"""
        if isinstance(data, dict):
            # Convertir permisos si es string
            if 'permisos' in data and isinstance(data['permisos'], str):
                try:
                    data['permisos'] = json.loads(data['permisos'])
                except json.JSONDecodeError:
                    data['permisos'] = {}
        return data
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "configuraciones_estado"
        indexes = ["posicion_orden", "nombre"]  # Índice simple, no único


class SubEstado(Document):
    """Sub-estados de un estado principal"""
    estado_id: ObjectId  # Referencia a ConfiguracionEstado
    nombre: str
    descripcion: Optional[str] = None
    posicion_orden: int
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "sub_estados"
        indexes = ["estado_id", "posicion_orden"]


class TransicionEstado(Document):
    """Transiciones permitidas entre estados"""
    estado_origen: ObjectId
    estado_destino: ObjectId
    roles_requeridos: List[str] = Field(default_factory=list)
    requiere_confirmacion: bool = False
    mensaje: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "transiciones_estado"
        indexes = ["estado_origen", "estado_destino"]


# ========================================
# Ejemplo de uso completo
# ========================================

"""
# Crear reclamo con datos embebidos
reclamo = Reclamo(
    asunto="Error crítico",
    nombre_cliente="Juan Pérez",
    info_contacto="juan@mail.com",
    descripcion="El sistema falla constantemente",
    estado_id=ObjectId("..."),
    prioridad="critical",
    creado_por=ObjectId("..."),
)

# Agregar comentario
reclamo.agregar_comentario(
    usuario_id=ObjectId("..."),
    usuario_nombre="Ana García",
    contenido="Estoy revisando el problema",
    es_interno=False
)

# Agregar nota
reclamo.agregar_nota(
    contenido="Cliente contactado por teléfono",
    autor="Ana García"
)

# Agregar adjunto
reclamo.agregar_adjunto(
    subido_por=ObjectId("..."),
    subido_por_nombre="Ana García",
    nombre_archivo="screenshot.png",
    url_archivo="https://storage.../screenshot.png",
    tipo_archivo="image/png",
    tamano_archivo=245678
)

# Registrar evento de auditoría
reclamo.registrar_evento(
    tipo_evento="cambio_estado",
    nombre_usuario="Ana García",
    usuario_id=ObjectId("..."),
    area_usuario="Soporte",
    cambios={"estado": {"de": "Nuevo", "a": "En Proceso"}},
    descripcion="Estado actualizado"
)

# Guardar en MongoDB (con todos los datos embebidos)
await reclamo.insert()

# Buscar reclamo con todos sus datos
reclamo = await Reclamo.get("507f1f77bcf86cd799439011")
print(f"Comentarios: {len(reclamo.comentarios)}")
print(f"Notas: {len(reclamo.notas)}")
print(f"Adjuntos: {len(reclamo.adjuntos)}")

# Actualizar comentario específico
reclamo = await Reclamo.get("507f1f77bcf86cd799439011")
reclamo.comentarios[0].contenido = "Contenido actualizado"
await reclamo.save()

# Búsqueda full-text
resultados = await Reclamo.buscar_texto("error facturación")

# Estadísticas
stats = await Reclamo.estadisticas_por_estado()
"""
