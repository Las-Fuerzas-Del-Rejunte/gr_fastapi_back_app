"""
Modelos de MongoDB para Clientes, Tipos de Proyecto y Proyectos
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field, EmailStr


class TipoProyecto(Document):
    """Modelo MongoDB de Tipo de Proyecto"""
    descripcion: str = Field(max_length=200)
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.now)
    actualizado_en: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "tipos_proyecto"
        indexes = [
            "descripcion",
        ]
    
    def __repr__(self):
        return f"<TipoProyecto {self.descripcion}>"


class Cliente(Document):
    """Modelo MongoDB de Cliente"""
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    telefono: Optional[str] = Field(None, max_length=50)
    correo: EmailStr = Field(unique=True)
    empresa: Optional[str] = Field(None, max_length=200)
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.now)
    actualizado_en: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "clientes"
        indexes = [
            "correo",
            "activo",
        ]
    
    def __repr__(self):
        return f"<Cliente {self.nombre} {self.apellido}>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del cliente"""
        return f"{self.nombre} {self.apellido}"


class Proyecto(Document):
    """Modelo MongoDB de Proyecto - Relación entre Cliente y Tipo de Proyecto"""
    nombre: str = Field(max_length=200)
    descripcion: Optional[str] = None
    cliente_id: PydanticObjectId = Field()  # ObjectId del cliente
    tipo_proyecto_id: PydanticObjectId = Field()  # ObjectId del tipo de proyecto
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.now)
    actualizado_en: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "proyectos"
        indexes = [
            "cliente_id",
            "tipo_proyecto_id",
            "activo",
        ]
    
    def __repr__(self):
        return f"<Proyecto {self.nombre}>"
