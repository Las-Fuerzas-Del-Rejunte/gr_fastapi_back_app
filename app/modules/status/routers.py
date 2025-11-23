"""
Router de Status Configs, SubEstados y Transiciones - Endpoints de la API
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.status.schemas import (
    ConfigEstadoCrear,
    ConfigEstadoRespuesta,
    ConfigEstadoActualizar,
    SubEstadoCrear,
    SubEstadoRespuesta,
    SubEstadoActualizar,
    TransicionEstadoCrear,
    TransicionEstadoRespuesta,
    TransicionEstadoActualizar,
    TransicionEstadoDetalle,
)
from app.modules.status.services import (
    StatusConfigService, 
    StatusNotFoundException,
    SubEstadoService,
    SubEstadoNotFoundException,
    TransicionEstadoService,
    TransicionEstadoNotFoundException,
)
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.users.models import UserRole
from app.core.exceptions import DuplicateException

router = APIRouter(prefix="/configuracion-estados", tags=["configuracion-estados"])


@router.get("", response_model=List[ConfigEstadoRespuesta])
async def listar_configuraciones_estado(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar todas las configuraciones de estado ordenadas por posición.
    
    Requiere autenticación.
    """
    configuraciones = await StatusConfigService.get_all(db)
    return configuraciones


@router.get("/{configuracion_id}", response_model=ConfigEstadoRespuesta)
async def obtener_configuracion_estado(
    configuracion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Obtener detalles de una configuración de estado.
    
    Requiere autenticación.
    """
    try:
        configuracion = await StatusConfigService.get_by_id(db, configuracion_id)
        
        if not configuracion:
            raise StatusNotFoundException(configuracion_id)
        
        return configuracion
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=ConfigEstadoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_configuracion_estado(
    datos_configuracion: ConfigEstadoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Crear nueva configuración de estado.
    
    Requiere rol de administrador.
    """
    try:
        configuracion = await StatusConfigService.create_status_config(db, datos_configuracion)
        return configuracion
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/{configuracion_id}", response_model=ConfigEstadoRespuesta)
async def actualizar_configuracion_estado(
    configuracion_id: UUID,
    datos_configuracion: ConfigEstadoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Actualizar configuración de estado.
    
    Requiere rol de administrador.
    """
    try:
        configuracion_actualizada = await StatusConfigService.update_status_config(db, configuracion_id, datos_configuracion)
        return configuracion_actualizada
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{configuracion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_configuracion_estado(
    configuracion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Eliminar configuración de estado.
    
    Requiere rol de administrador.
    """
    try:
        await StatusConfigService.delete_status_config(db, configuracion_id)
        return None
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# ENDPOINTS DE SUB-ESTADOS
# ============================================

@router.get("/sub-estados", response_model=List[SubEstadoRespuesta])
async def listar_sub_estados(
    estado_id: Optional[UUID] = Query(None, description="Filtrar por estado padre"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar todos los sub-estados, opcionalmente filtrados por estado.
    
    Requiere autenticación.
    """
    sub_estados = await SubEstadoService.get_all(db, estado_id=estado_id)
    return sub_estados


@router.get("/sub-estados/{sub_estado_id}", response_model=SubEstadoRespuesta)
async def obtener_sub_estado(
    sub_estado_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Obtener detalles de un sub-estado.
    
    Requiere autenticación.
    """
    try:
        sub_estado = await SubEstadoService.get_by_id(db, sub_estado_id, load_relations=True)
        
        if not sub_estado:
            raise SubEstadoNotFoundException(sub_estado_id)
        
        return sub_estado
    except SubEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{estado_id}/sub-estados", response_model=List[SubEstadoRespuesta])
async def listar_sub_estados_por_estado(
    estado_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar sub-estados de un estado específico.
    
    Requiere autenticación.
    """
    try:
        # Verificar que el estado existe
        estado = await StatusConfigService.get_by_id(db, estado_id)
        if not estado:
            raise StatusNotFoundException(estado_id)
        
        sub_estados = await SubEstadoService.get_by_estado(db, estado_id)
        return sub_estados
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/sub-estados", response_model=SubEstadoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_sub_estado(
    datos_sub_estado: SubEstadoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Crear nuevo sub-estado.
    
    Requiere rol de administrador.
    """
    try:
        sub_estado = await SubEstadoService.create(db, datos_sub_estado)
        return sub_estado
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/sub-estados/{sub_estado_id}", response_model=SubEstadoRespuesta)
async def actualizar_sub_estado(
    sub_estado_id: UUID,
    datos_sub_estado: SubEstadoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Actualizar sub-estado.
    
    Requiere rol de administrador.
    """
    try:
        sub_estado_actualizado = await SubEstadoService.update(db, sub_estado_id, datos_sub_estado)
        return sub_estado_actualizado
    except SubEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/sub-estados/{sub_estado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sub_estado(
    sub_estado_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Eliminar sub-estado.
    
    Requiere rol de administrador.
    """
    try:
        await SubEstadoService.delete(db, sub_estado_id)
        return None
    except SubEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# ENDPOINTS DE TRANSICIONES DE ESTADO
# ============================================

@router.get("/transiciones", response_model=List[TransicionEstadoDetalle])
async def listar_transiciones(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar todas las transiciones de estado.
    
    Requiere autenticación.
    """
    transiciones = await TransicionEstadoService.get_all(db, load_relations=True)
    
    # Enriquecer con nombres de estados
    transiciones_detalle = []
    for trans in transiciones:
        trans_dict = TransicionEstadoDetalle.model_validate(trans).model_dump()
        trans_dict['desde_estado_nombre'] = trans.estado_origen.nombre if trans.estado_origen else None
        trans_dict['hacia_estado_nombre'] = trans.estado_destino.nombre if trans.estado_destino else None
        trans_dict['desde_estado_color'] = trans.estado_origen.color if trans.estado_origen else None
        trans_dict['hacia_estado_color'] = trans.estado_destino.color if trans.estado_destino else None
        transiciones_detalle.append(TransicionEstadoDetalle(**trans_dict))
    
    return transiciones_detalle


@router.get("/transiciones/{transicion_id}", response_model=TransicionEstadoDetalle)
async def obtener_transicion(
    transicion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Obtener detalles de una transición.
    
    Requiere autenticación.
    """
    try:
        transicion = await TransicionEstadoService.get_by_id(db, transicion_id, load_relations=True)
        
        if not transicion:
            raise TransicionEstadoNotFoundException(transicion_id)
        
        # Enriquecer con nombres de estados
        trans_dict = TransicionEstadoDetalle.model_validate(transicion).model_dump()
        trans_dict['desde_estado_nombre'] = transicion.estado_origen.nombre if transicion.estado_origen else None
        trans_dict['hacia_estado_nombre'] = transicion.estado_destino.nombre if transicion.estado_destino else None
        trans_dict['desde_estado_color'] = transicion.estado_origen.color if transicion.estado_origen else None
        trans_dict['hacia_estado_color'] = transicion.estado_destino.color if transicion.estado_destino else None
        
        return TransicionEstadoDetalle(**trans_dict)
    except TransicionEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/transiciones/desde/{estado_id}", response_model=List[TransicionEstadoDetalle])
async def listar_transiciones_desde_estado(
    estado_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar transiciones válidas desde un estado específico.
    
    Útil para mostrar qué estados se pueden alcanzar desde el estado actual de un reclamo.
    
    Requiere autenticación.
    """
    try:
        # Verificar que el estado existe
        estado = await StatusConfigService.get_by_id(db, estado_id)
        if not estado:
            raise StatusNotFoundException(estado_id)
        
        transiciones = await TransicionEstadoService.get_transiciones_desde_estado(db, estado_id)
        
        # Enriquecer con nombres de estados
        transiciones_detalle = []
        for trans in transiciones:
            trans_dict = TransicionEstadoDetalle.model_validate(trans).model_dump()
            trans_dict['desde_estado_nombre'] = trans.estado_origen.nombre if trans.estado_origen else None
            trans_dict['hacia_estado_nombre'] = trans.estado_destino.nombre if trans.estado_destino else None
            trans_dict['desde_estado_color'] = trans.estado_origen.color if trans.estado_origen else None
            trans_dict['hacia_estado_color'] = trans.estado_destino.color if trans.estado_destino else None
            transiciones_detalle.append(TransicionEstadoDetalle(**trans_dict))
        
        return transiciones_detalle
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/transiciones", response_model=TransicionEstadoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_transicion(
    datos_transicion: TransicionEstadoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Crear nueva transición de estado.
    
    Requiere rol de administrador.
    """
    try:
        transicion = await TransicionEstadoService.create(db, datos_transicion)
        return transicion
    except StatusNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/transiciones/{transicion_id}", response_model=TransicionEstadoRespuesta)
async def actualizar_transicion(
    transicion_id: UUID,
    datos_transicion: TransicionEstadoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Actualizar transición de estado.
    
    Requiere rol de administrador.
    """
    try:
        transicion_actualizada = await TransicionEstadoService.update(db, transicion_id, datos_transicion)
        return transicion_actualizada
    except TransicionEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/transiciones/{transicion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_transicion(
    transicion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN)),
):
    """
    Eliminar transición de estado.
    
    Requiere rol de administrador.
    """
    try:
        await TransicionEstadoService.delete(db, transicion_id)
        return None
    except TransicionEstadoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
