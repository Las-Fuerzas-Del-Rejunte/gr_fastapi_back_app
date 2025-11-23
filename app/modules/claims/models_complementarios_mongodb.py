"""
Modelos complementarios de MongoDB: Cliente, TipoProyecto, Proyecto
Estos modelos se separaron para mejor organización
"""
from beanie import Document
from pydantic import EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, Annotated
from beanie import Indexed
from bson import ObjectId


class Cliente(Document):
    """
    Modelo de Cliente para MongoDB
    Colección: clientes
    """
    nombre: str
    email: Optional[EmailStr] = None  # Removido índice único para permitir null
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    contacto_principal: Optional[str] = None
    sitio_web: Optional[str] = None
    notas: Optional[str] = None
    activo: bool = True
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "clientes"
        indexes = ["nombre", "activo", "email"]  # Índice simple, no único


class TipoProyecto(Document):
    """
    Modelo de Tipo de Proyecto para MongoDB
    Colección: tipos_proyecto
    """
    nombre: str  # Removido índice único
    descripcion: Optional[str] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    activo: bool = True
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "tipos_proyecto"
        indexes = ["activo", "nombre"]  # Índice simple, no único


class Proyecto(Document):
    """
    Modelo de Proyecto para MongoDB
    Colección: proyectos
    """
    nombre: str
    descripcion: Optional[str] = None
    cliente_id: ObjectId  # Referencia a Cliente
    tipo_proyecto_id: ObjectId  # Referencia a TipoProyecto
    
    # Información del proyecto
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: str = "activo"  # activo, pausado, completado, cancelado
    prioridad: str = "medium"  # low, medium, high, critical
    
    # Equipo y responsables
    manager_id: Optional[ObjectId] = None  # Referencia a Usuario
    miembros_equipo: list[ObjectId] = Field(default_factory=list)  # Referencias a Usuarios
    
    # Metadata
    presupuesto: Optional[float] = None
    horas_estimadas: Optional[int] = None
    horas_trabajadas: Optional[int] = None
    notas: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    
    # Timestamps
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "proyectos"
        indexes = [
            "cliente_id",
            "tipo_proyecto_id",
            "estado",
            "manager_id",
            [("cliente_id", 1), ("estado", 1)],
            [("fecha_inicio", -1)],
        ]
