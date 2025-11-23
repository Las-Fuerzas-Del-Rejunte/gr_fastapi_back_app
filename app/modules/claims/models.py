"""
Modelos de Reclamo (Claim) y relacionados
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Enum, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.models import BaseModel


class ClaimPriority(str, PyEnum):
    """Prioridades de reclamo"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Cambiado de URGENT a CRITICAL para coincidir con la guía


class Claim(BaseModel):
    """
    Modelo de Reclamo
    
    Tabla: reclamos
    """
    __tablename__ = "reclamos"
    
    # Campos básicos
    asunto = Column(String(500), nullable=False)
    nombre_cliente = Column(String(255), nullable=False)
    info_contacto = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Estado: FK directo a configuraciones_estado (diseño correcto)
    estado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("configuraciones_estado.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # prioridad como VARCHAR con CHECK (coincide con Supabase)
    prioridad = Column(
        String(50),
        nullable=True,
        default="medium",
        index=True
    )
    
    # Nuevos campos agregados - UUID nativo (no String)
    sub_estado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sub_estados.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    categoria = Column(String(100), nullable=True)  # Categoría del reclamo
    email_cliente = Column(String(255), nullable=True)  # Email adicional del cliente
    telefono_cliente = Column(String(50), nullable=True)  # Teléfono adicional del cliente
    resumen_resolucion = Column(Text, nullable=True)  # Resumen al cerrar el reclamo
    bloqueado = Column(Boolean, default=False, nullable=False, index=True)  # Si está bloqueado para edición
    resuelto_en = Column(DateTime, nullable=True)  # Fecha de resolución
    
    # Foreign Keys
    creado_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    asignado_a = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Foreign Key a Proyecto
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relaciones
    creador = relationship(
        "User",
        back_populates="reclamos_creados",
        foreign_keys=[creado_por]
    )
    
    agente_asignado = relationship(
        "User",
        back_populates="reclamos_asignados",
        foreign_keys=[asignado_a]
    )
    
    # Relación con configuración de estado (OBLIGATORIA)
    estado_config = relationship(
        "StatusConfig",
        foreign_keys=[estado_id],
        lazy="joined"  # Cargar siempre para tener nombre y color
    )
    
    # Relación con sub-estado (opcional)
    sub_estado_config = relationship(
        "SubEstado",
        foreign_keys=[sub_estado_id],
        lazy="joined"
    )
    
    # Relación con proyecto
    proyecto = relationship(
        "Proyecto",
        back_populates="reclamos",
        foreign_keys=[proyecto_id],
        lazy="joined"
    )
    
    # Nuevas relaciones
    eventos_auditoria = relationship(
        "EventoAuditoria",
        back_populates="reclamo",
        cascade="all, delete-orphan",
        order_by="EventoAuditoria.creado_en.desc()"
    )
    
    comentarios = relationship(
        "ComentarioReclamo",
        back_populates="reclamo",
        cascade="all, delete-orphan",
        order_by="ComentarioReclamo.creado_en.desc()"
    )
    
    adjuntos = relationship(
        "AdjuntoReclamo",
        back_populates="reclamo",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        estado_nombre = self.estado_config.nombre if self.estado_config else str(self.estado_id)
        return f"<Claim {self.asunto} ({estado_nombre})>"


class EventoAuditoria(BaseModel):
    """
    Modelo de Evento de Auditoría (nuevo)
    Registra todos los cambios realizados en un reclamo
    
    Tabla: eventos_auditoria
    """
    __tablename__ = "eventos_auditoria"
    
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tipo_evento = Column(String(50), nullable=False, index=True)  # created, status_changed, assigned, etc.
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nombre_usuario = Column(String(255), nullable=False)
    area_usuario = Column(String(100), nullable=True)
    cambios = Column(JSONB, nullable=True)  # JSON con detalles de los cambios
    descripcion = Column(Text, nullable=True)
    
    # Relaciones
    reclamo = relationship("Claim", back_populates="eventos_auditoria")
    
    def __repr__(self):
        return f"<EventoAuditoria {self.tipo_evento} en Reclamo {self.reclamo_id}>"


class ComentarioReclamo(BaseModel):
    """
    Modelo de Comentario en Reclamo (nuevo)
    Permite agregar comentarios públicos o internos a un reclamo
    
    Tabla: comentarios_reclamo
    """
    __tablename__ = "comentarios_reclamo"
    
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contenido = Column(Text, nullable=False)
    es_interno = Column(Boolean, default=False, nullable=False)  # Si es visible solo para el equipo
    
    # Relaciones
    reclamo = relationship("Claim", back_populates="comentarios")
    usuario = relationship("User")
    
    def __repr__(self):
        return f"<ComentarioReclamo en Reclamo {self.reclamo_id}>"


class AdjuntoReclamo(BaseModel):
    """
    Modelo de Archivo Adjunto (nuevo)
    Permite adjuntar archivos a un reclamo
    
    Tabla: adjuntos_reclamo
    """
    __tablename__ = "adjuntos_reclamo"
    
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subido_por = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False
    )
    nombre_archivo = Column(String(255), nullable=False)
    url_archivo = Column(Text, nullable=False)  # URL o path del archivo
    tipo_archivo = Column(String(100), nullable=True)  # MIME type
    tamano_archivo = Column(Integer, nullable=True)  # Tamaño en bytes
    
    # Relaciones
    reclamo = relationship("Claim", back_populates="adjuntos")
    usuario = relationship("User")
    
    def __repr__(self):
        return f"<AdjuntoReclamo {self.nombre_archivo}>"
