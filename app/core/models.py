"""
Modelos base y mixins comunes para todos los modelos
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UUIDMixin:
    """Mixin para agregar ID UUID como primary key"""
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )


class TimestampMixin:
    """
    Mixin para agregar timestamps de creación y actualización
    IMPORTANTE: Usa timezone=False para coincidir con Supabase
    (timestamp without time zone)
    """
    creado_en = Column(
        DateTime(timezone=False),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False
    )
    actualizado_en = Column(
        DateTime(timezone=False),
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Modelo base abstracto que combina UUID y Timestamps
    Todos los modelos deben heredar de esta clase
    """
    __abstract__ = True
