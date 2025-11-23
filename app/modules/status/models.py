"""
Modelos de Configuración de Estado
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.models import BaseModel


class StatusConfig(BaseModel):
    """
    Modelo de Configuración de Estado
    
    Tabla: configuraciones_estado
    """
    __tablename__ = "configuraciones_estado"
    
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(50), nullable=False)
    posicion_orden = Column(Integer, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)  # Nuevo campo
    area = Column(String(100), nullable=True)  # Nuevo campo
    permisos = Column(JSONB, nullable=False, default={})  # Nuevo campo para permisos dinámicos
    
    # Relaciones
    sub_estados = relationship(
        "SubEstado",
        back_populates="estado_padre",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<StatusConfig {self.nombre} (orden: {self.posicion_orden})>"


class SubEstado(BaseModel):
    """
    Modelo de Sub-Estado (nuevo)
    Permite tener estados más granulares dentro de un estado principal
    
    Tabla: sub_estados
    IMPORTANTE: estado_id debe ser UUID nativo (no String)
    """
    __tablename__ = "sub_estados"
    
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    posicion_orden = Column(Integer, nullable=False)
    estado_id = Column(
        ForeignKey("configuraciones_estado.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relaciones
    estado_padre = relationship("StatusConfig", back_populates="sub_estados")
    
    def __repr__(self):
        return f"<SubEstado {self.nombre}>"


class TransicionEstado(BaseModel):
    """
    Modelo de Transición de Estados (nuevo)
    Define qué transiciones de estado son válidas y quién puede ejecutarlas
    
    Tabla: transiciones_estado
    IMPORTANTE: estado_origen y estado_destino deben ser UUID nativos (no String)
    """
    __tablename__ = "transiciones_estado"
    
    estado_origen = Column(
        ForeignKey("configuraciones_estado.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    estado_destino = Column(
        ForeignKey("configuraciones_estado.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    roles_requeridos = Column(JSONB, default=[])  # Lista de roles que pueden hacer la transición
    requiere_confirmacion = Column(Boolean, default=False)  # Si requiere confirmación del usuario
    mensaje = Column(Text, nullable=True)  # Mensaje a mostrar al usuario
    
    def __repr__(self):
        return f"<TransicionEstado {self.estado_origen} -> {self.estado_destino}>"
