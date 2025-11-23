"""
Modelos de Clientes y Proyectos
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoProyecto(Base):
    """Modelo de Tipo de Proyecto"""
    __tablename__ = "tipos_proyecto"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    descripcion: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    
    # Timestamps
    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # Relaciones
    proyectos: Mapped[list["Proyecto"]] = relationship(
        "Proyecto",
        back_populates="tipo_proyecto"
    )
    
    def __repr__(self):
        return f"<TipoProyecto {self.descripcion}>"


class Cliente(Base):
    """Modelo de Cliente"""
    __tablename__ = "clientes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    empresa: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)
    
    # Timestamps
    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # Relaciones
    proyectos: Mapped[list["Proyecto"]] = relationship(
        "Proyecto",
        back_populates="cliente"
    )
    
    def __repr__(self):
        return f"<Cliente {self.nombre} {self.apellido}>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del cliente"""
        return f"{self.nombre} {self.apellido}"


class Proyecto(Base):
    """Modelo de Proyecto - Relación entre Cliente y Tipo de Proyecto"""
    __tablename__ = "proyectos"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign Keys
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False
    )
    tipo_proyecto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tipos_proyecto.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    activo: Mapped[bool] = mapped_column(default=True)
    
    # Timestamps
    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # Relaciones
    cliente: Mapped["Cliente"] = relationship(
        "Cliente",
        back_populates="proyectos"
    )
    tipo_proyecto: Mapped["TipoProyecto"] = relationship(
        "TipoProyecto",
        back_populates="proyectos"
    )
    reclamos: Mapped[list["Claim"]] = relationship(
        "Claim",
        back_populates="proyecto"
    )
    
    def __repr__(self):
        return f"<Proyecto {self.nombre}>"
