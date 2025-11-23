"""
Schemas de paginación reutilizables
"""
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ParametrosPaginacion(BaseModel):
    """Parámetros de paginación para queries"""
    pagina: int = Field(default=1, ge=1, description="Número de página")
    limite: int = Field(default=20, ge=1, le=100, description="Items por página")


class MetaPaginacion(BaseModel):
    """Metadata de paginación en responses"""
    pagina: int = Field(description="Página actual")
    limite: int = Field(description="Items por página")
    total: int = Field(description="Total de items")
    total_paginas: int = Field(description="Total de páginas")


class RespuestaPaginada(BaseModel, Generic[T]):
    """
    Response genérico paginado
    
    Ejemplo:
        RespuestaPaginada[ReclamoRespuesta] para reclamos paginados
    """
    datos: List[T] = Field(description="Lista de items")
    paginacion: MetaPaginacion = Field(description="Información de paginación")


# Mantener compatibilidad con nombres en inglés (deprecated)
PaginationParams = ParametrosPaginacion
PaginationMeta = MetaPaginacion
PaginatedResponse = RespuestaPaginada
