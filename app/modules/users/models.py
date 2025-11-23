"""
Modelo de Usuario
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, String, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.models import BaseModel


class UserRole(str, PyEnum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class User(BaseModel):
    """
    Modelo de Usuario/Agente
    
    Tabla: usuarios
    IMPORTANTE: Este modelo está adaptado al esquema existente en Supabase
    - rol es VARCHAR con CHECK constraint (no ENUM nativo)
    - activo es VARCHAR (no BOOLEAN)
    """
    __tablename__ = "usuarios"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    
    # rol como VARCHAR con CHECK constraint (coincide con Supabase)
    rol = Column(
        String(50),
        CheckConstraint(
            "rol IN ('admin', 'manager', 'agent', 'viewer')",
            name="usuarios_rol_check"
        ),
        nullable=False,
        default="agent",
        index=True
    )
    
    telefono = Column(String(50), nullable=True)
    departamento = Column(String(100), nullable=True)
    posicion = Column(String(100), nullable=True)
    area = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # activo como VARCHAR (coincide con Supabase: 'true'/'false' como strings)
    activo = Column(
        String(10),
        nullable=False,
        default="true",
        index=True
    )
    
    # Relaciones
    reclamos_creados = relationship(
        "Claim",
        back_populates="creador",
        foreign_keys="Claim.creado_por"
    )
    
    reclamos_asignados = relationship(
        "Claim",
        back_populates="agente_asignado",
        foreign_keys="Claim.asignado_a"
    )
    
    def __repr__(self):
        return f"<User {self.email} ({self.rol})>"
