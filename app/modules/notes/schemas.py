"""
Schemas de Nota (ClaimNote)
"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Request Schemas
# ============================================

class NotaReclamoCrear(BaseModel):
    """Schema para crear nota"""
    contenido: str = Field(min_length=1, description="Contenido de la nota")
    autor: str = Field(min_length=1, max_length=255, description="Autor de la nota")


class NotaReclamoActualizar(BaseModel):
    """Schema para actualizar nota"""
    contenido: str = Field(min_length=1, description="Contenido de la nota")


# ============================================
# Response Schemas
# ============================================

class NotaReclamoRespuesta(BaseModel):
    """Schema de respuesta de nota"""
    id: UUID = Field(description="ID único de la nota")
    reclamo_id: UUID = Field(description="ID del reclamo")
    contenido: str = Field(description="Contenido de la nota")
    autor: str = Field(description="Autor de la nota")
    creado_en: datetime = Field(description="Fecha de creación")
    actualizado_en: datetime = Field(description="Última actualización")
    
    model_config = ConfigDict(from_attributes=True)
