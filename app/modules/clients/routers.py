"""
Router de Clientes y Proyectos - Endpoints de la API
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.clients.schemas import (
    ClienteCrear,
    ClienteActualizar,
    ClienteRespuesta,
    TipoProyectoCrear,
    TipoProyectoActualizar,
    TipoProyectoRespuesta,
    ProyectoCrear,
    ProyectoActualizar,
    ProyectoRespuesta,
)
from app.modules.clients.services import ClienteService, TipoProyectoService, ProyectoService

# Routers
router_clientes = APIRouter(prefix="/clientes", tags=["clientes"])
router_tipos_proyecto = APIRouter(prefix="/tipos-proyecto", tags=["tipos-proyecto"])
router_proyectos = APIRouter(prefix="/proyectos", tags=["proyectos"])


# ============================================
# ENDPOINTS DE CLIENTES
# ============================================

@router_clientes.get("", response_model=List[ClienteRespuesta])
async def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los clientes"""
    clientes = await ClienteService.listar(db, skip=skip, limit=limit, solo_activos=solo_activos)
    return clientes


@router_clientes.get("/{cliente_id}", response_model=ClienteRespuesta)
async def obtener_cliente(
    cliente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Obtener un cliente por ID"""
    cliente = await ClienteService.obtener_por_id(db, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return cliente


@router_clientes.post("", response_model=ClienteRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    cliente_data: ClienteCrear,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo cliente"""
    # Verificar si el correo ya existe
    cliente_existente = await ClienteService.obtener_por_correo(db, cliente_data.correo)
    if cliente_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con ese correo electrónico"
        )
    
    cliente = await ClienteService.crear(db, cliente_data.model_dump())
    return cliente


@router_clientes.put("/{cliente_id}", response_model=ClienteRespuesta)
async def actualizar_cliente(
    cliente_id: uuid.UUID,
    cliente_data: ClienteActualizar,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un cliente existente"""
    # Si se está actualizando el correo, verificar que no exista
    if cliente_data.correo:
        cliente_con_correo = await ClienteService.obtener_por_correo(db, cliente_data.correo)
        if cliente_con_correo and cliente_con_correo.id != cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese correo electrónico"
            )
    
    cliente = await ClienteService.actualizar(
        db,
        cliente_id,
        cliente_data.model_dump(exclude_unset=True)
    )
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return cliente


@router_clientes.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_cliente(
    cliente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Desactivar un cliente"""
    eliminado = await ClienteService.eliminar(db, cliente_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return None


# ============================================
# ENDPOINTS DE TIPOS DE PROYECTO
# ============================================

@router_tipos_proyecto.get("", response_model=List[TipoProyectoRespuesta])
async def listar_tipos_proyecto(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los tipos de proyecto"""
    tipos = await TipoProyectoService.listar(db, skip=skip, limit=limit, solo_activos=solo_activos)
    return tipos


@router_tipos_proyecto.get("/{tipo_id}", response_model=TipoProyectoRespuesta)
async def obtener_tipo_proyecto(
    tipo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Obtener un tipo de proyecto por ID"""
    tipo = await TipoProyectoService.obtener_por_id(db, tipo_id)
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    return tipo


@router_tipos_proyecto.post("", response_model=TipoProyectoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_tipo_proyecto(
    tipo_data: TipoProyectoCrear,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo tipo de proyecto"""
    tipo = await TipoProyectoService.crear(db, tipo_data.model_dump())
    return tipo


@router_tipos_proyecto.put("/{tipo_id}", response_model=TipoProyectoRespuesta)
async def actualizar_tipo_proyecto(
    tipo_id: uuid.UUID,
    tipo_data: TipoProyectoActualizar,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un tipo de proyecto existente"""
    tipo = await TipoProyectoService.actualizar(
        db,
        tipo_id,
        tipo_data.model_dump(exclude_unset=True)
    )
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    return tipo


# ============================================
# ENDPOINTS DE PROYECTOS
# ============================================

@router_proyectos.get("", response_model=List[ProyectoRespuesta])
async def listar_proyectos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los proyectos"""
    proyectos = await ProyectoService.listar(db, skip=skip, limit=limit, solo_activos=solo_activos)
    return proyectos


@router_proyectos.get("/cliente/{cliente_id}", response_model=List[ProyectoRespuesta])
async def listar_proyectos_por_cliente(
    cliente_id: uuid.UUID,
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Listar proyectos de un cliente específico"""
    proyectos = await ProyectoService.listar_por_cliente(db, cliente_id, solo_activos=solo_activos)
    return proyectos


@router_proyectos.get("/{proyecto_id}", response_model=ProyectoRespuesta)
async def obtener_proyecto(
    proyecto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Obtener un proyecto por ID"""
    proyecto = await ProyectoService.obtener_por_id(db, proyecto_id)
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    return proyecto


@router_proyectos.post("", response_model=ProyectoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_proyecto(
    proyecto_data: ProyectoCrear,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo proyecto"""
    # Verificar que el cliente existe
    cliente = await ClienteService.obtener_por_id(db, proyecto_data.cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar que el tipo de proyecto existe
    tipo = await TipoProyectoService.obtener_por_id(db, proyecto_data.tipo_proyecto_id)
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    proyecto = await ProyectoService.crear(db, proyecto_data.model_dump())
    return proyecto


@router_proyectos.put("/{proyecto_id}", response_model=ProyectoRespuesta)
async def actualizar_proyecto(
    proyecto_id: uuid.UUID,
    proyecto_data: ProyectoActualizar,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un proyecto existente"""
    proyecto = await ProyectoService.actualizar(
        db,
        proyecto_id,
        proyecto_data.model_dump(exclude_unset=True)
    )
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    return proyecto


@router_proyectos.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_proyecto(
    proyecto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    usuario_actual = Depends(get_current_user),
):
    """Desactivar un proyecto"""
    eliminado = await ProyectoService.eliminar(db, proyecto_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    return None
