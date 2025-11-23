"""
Router de Reclamos, Comentarios, Adjuntos y Auditoría - Endpoints de la API
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import PaginatedResponse, PaginationMeta
from app.modules.claims.models import ClaimPriority
from app.modules.claims.schemas import (
    ReclamoCrear,
    ReclamoRespuesta,
    ReclamoActualizar,
    ReclamoItemLista,
    ReclamoDetalle,
    ReclamoAsignar,
    EventoAuditoriaRespuesta,
    ComentarioReclamoCrear,
    ComentarioReclamoRespuesta,
    ComentarioReclamoActualizar,
    AdjuntoReclamoCrear,
    AdjuntoReclamoRespuesta,
)
from app.modules.claims.services import (
    ClaimService,
    EventoAuditoriaService,
    ComentarioReclamoService,
    ComentarioReclamoNotFoundException,
    AdjuntoReclamoService,
    AdjuntoReclamoNotFoundException,
)
from app.modules.auth.dependencies import get_current_user
from app.core.exceptions import ClaimNotFoundException, UserNotFoundException

router = APIRouter(prefix="/reclamos", tags=["reclamos"])


@router.get("", response_model=PaginatedResponse[ReclamoItemLista])
async def listar_reclamos(
    estado: Optional[str] = Query(None, description="Filtrar por estado (UUID o nombre)"),
    asignado_a: Optional[UUID] = Query(None, description="Filtrar por agente asignado"),
    prioridad: Optional[ClaimPriority] = Query(None, description="Filtrar por prioridad"),
    buscar: Optional[str] = Query(None, description="Buscar en asunto y nombre de cliente"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    limite: int = Query(20, ge=1, le=100, description="Items por página"),
    ordenar_por: str = Query("created_at", description="Campo para ordenar"),
    orden: str = Query("desc", regex="^(asc|desc)$", description="Orden"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar todos los reclamos con filtros y paginación.
    
    Requiere autenticación.
    """
    skip = (pagina - 1) * limite
    
    reclamos, total = await ClaimService.get_all(
        db=db,
        status=estado,
        assigned_to=asignado_a,
        priority=prioridad,
        search=buscar,
        skip=skip,
        limit=limite,
        sort_by=ordenar_por,
        sort_order=orden,
    )
    
    # Obtener conteos de comentarios y adjuntos de forma eficiente (sin cargar las relaciones completas)
    reclamos_con_conteo = []
    for reclamo in reclamos:
        reclamo_dict = ReclamoItemLista.model_validate(reclamo)
        # Contadores en 0 por defecto (se pueden cargar con una query adicional si es necesario)
        reclamo_dict.cantidad_comentarios = 0
        reclamo_dict.cantidad_adjuntos = 0
        reclamos_con_conteo.append(reclamo_dict)
    
    total_paginas = (total + limite - 1) // limite
    
    return {
        "datos": reclamos_con_conteo,
        "paginacion": PaginationMeta(
            pagina=pagina,
            limite=limite,
            total=total,
            total_paginas=total_paginas,
        )
    }


@router.get("/{reclamo_id}", response_model=ReclamoDetalle)
async def obtener_reclamo(
    reclamo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Obtener detalles completos de un reclamo.
    
    Requiere autenticación.
    """
    try:
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=True)
        
        if not reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        return reclamo
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=ReclamoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_reclamo(
    datos_reclamo: ReclamoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Crear nuevo reclamo.
    
    Requiere autenticación.
    """
    try:
        reclamo = await ClaimService.create_claim(db, datos_reclamo)
        
        # Crear evento de auditoría de creación
        await db.refresh(reclamo, ["estado_config"])
        await EventoAuditoriaService.crear_evento(
            db,
            reclamo_id=reclamo.id,
            tipo_evento="created",
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area,
            descripcion=f"Reclamo creado en estado '{reclamo.estado_config.nombre}'"
        )
        await db.commit()
        
        return reclamo
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )



@router.patch("/{reclamo_id}", response_model=ReclamoRespuesta)
async def actualizar_reclamo(
    reclamo_id: UUID,
    datos_reclamo: ReclamoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Actualizar reclamo (estado, prioridad, etc).
    
    Requiere autenticación.
    Retorna solo datos básicos del reclamo para mejor rendimiento.
    """
    try:
        # Obtener reclamo actual para comparar cambios
        reclamo_anterior = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo_anterior:
            raise ClaimNotFoundException(reclamo_id)
        
        # Actualizar reclamo
        reclamo_actualizado = await ClaimService.update_claim(db, reclamo_id, datos_reclamo)
        
        # Crear eventos de auditoría según los cambios
        cambios_dict = datos_reclamo.model_dump(exclude_unset=True)
        
        if cambios_dict:
            # Detectar tipo de evento principal
            tipo_evento = "updated"
            descripcion_partes = []
            
            if "estado_id" in cambios_dict:
                tipo_evento = "status_changed"
                # Cargar estado nuevo para la descripción
                await db.refresh(reclamo_actualizado, ["estado_config"])
                descripcion_partes.append(f"Estado cambiado a '{reclamo_actualizado.estado_config.nombre}'")
            
            if "sub_estado_id" in cambios_dict:
                # Si es el único cambio, es un cambio de sub-estado
                if len(cambios_dict) == 1:
                    tipo_evento = "sub_status_changed"
                # Cargar sub-estado nuevo para la descripción
                await db.refresh(reclamo_actualizado, ["sub_estado_config"])
                if reclamo_actualizado.sub_estado_config:
                    descripcion_partes.append(f"Sub-estado cambiado a '{reclamo_actualizado.sub_estado_config.nombre}'")
                else:
                    descripcion_partes.append("Sub-estado removido")
            
            if "prioridad" in cambios_dict:
                descripcion_partes.append(f"Prioridad cambiada a '{cambios_dict['prioridad']}'")
            
            if "asignado_a" in cambios_dict:
                # Si es el único cambio, marcar como asignación
                if len(cambios_dict) == 1:
                    tipo_evento = "assigned"
                await db.refresh(reclamo_actualizado, ["agente_asignado"])
                if reclamo_actualizado.agente_asignado:
                    descripcion_partes.append(f"Asignado a {reclamo_actualizado.agente_asignado.nombre}")
                else:
                    descripcion_partes.append("Desasignado")
            
            descripcion = ", ".join(descripcion_partes) if descripcion_partes else "Reclamo actualizado"
            
            # Crear evento de auditoría
            await EventoAuditoriaService.crear_evento(
                db,
                reclamo_id=reclamo_id,
                tipo_evento=tipo_evento,
                usuario_id=current_user.id,
                nombre_usuario=current_user.nombre,
                area_usuario=current_user.area,
                cambios=cambios_dict,
                descripcion=descripcion
            )
            
            await db.commit()
        
        return reclamo_actualizado
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{reclamo_id}/asignar", response_model=ReclamoDetalle)
async def asignar_reclamo(
    reclamo_id: UUID,
    datos_asignacion: ReclamoAsignar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Asignar reclamo a un agente.
    
    Requiere autenticación.
    """
    try:
        reclamo_actualizado = await ClaimService.assign_agent_to_claim(db, reclamo_id, datos_asignacion.agente_id)
        
        # Crear evento de auditoría de asignación
        await db.refresh(reclamo_actualizado, ["agente_asignado"])
        await EventoAuditoriaService.crear_evento(
            db,
            reclamo_id=reclamo_id,
            tipo_evento="assigned",
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area,
            cambios={"asignado_a": str(datos_asignacion.agente_id)},
            descripcion=f"Asignado a {reclamo_actualizado.agente_asignado.nombre if reclamo_actualizado.agente_asignado else 'sin asignar'}"
        )
        await db.commit()
        
        return reclamo_actualizado
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{reclamo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_reclamo(
    reclamo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Eliminar reclamo.
    
    Requiere autenticación.
    """
    try:
        # Obtener información del reclamo antes de eliminarlo
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        # Crear evento de auditoría de eliminación ANTES de eliminar
        await EventoAuditoriaService.crear_evento(
            db,
            reclamo_id=reclamo_id,
            tipo_evento="deleted",
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area,
            descripcion=f"Reclamo eliminado: {reclamo.asunto}"
        )
        await db.commit()
        
        # Ahora eliminar el reclamo (el evento ya está guardado)
        await ClaimService.delete_claim(db, reclamo_id)
        return None
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# ENDPOINTS DE EVENTOS DE AUDITORÍA
# ============================================

@router.get("/{reclamo_id}/auditoria", response_model=List[EventoAuditoriaRespuesta])
async def listar_eventos_auditoria(
    reclamo_id: UUID,
    limite: Optional[int] = Query(None, ge=1, le=100, description="Cantidad máxima de eventos"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Obtener historial de eventos de auditoría de un reclamo.
    
    Los eventos están ordenados por fecha descendente (más recientes primero).
    
    Requiere autenticación.
    """
    try:
        # Verificar que el reclamo existe
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        eventos = await EventoAuditoriaService.get_by_reclamo(db, reclamo_id, limite=limite)
        return eventos
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# ENDPOINTS DE COMENTARIOS
# ============================================

@router.get("/{reclamo_id}/comentarios", response_model=List[ComentarioReclamoRespuesta])
async def listar_comentarios(
    reclamo_id: UUID,
    incluir_internos: bool = Query(True, description="Incluir comentarios internos"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar comentarios de un reclamo.
    
    Los comentarios están ordenados por fecha descendente (más recientes primero).
    
    Requiere autenticación.
    """
    try:
        # Verificar que el reclamo existe
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        comentarios = await ComentarioReclamoService.get_by_reclamo(
            db, 
            reclamo_id, 
            incluir_internos=incluir_internos
        )
        return comentarios
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{reclamo_id}/comentarios", response_model=ComentarioReclamoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_comentario(
    reclamo_id: UUID,
    datos_comentario: ComentarioReclamoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Agregar comentario a un reclamo.
    
    Requiere autenticación.
    """
    try:
        comentario = await ComentarioReclamoService.crear(
            db,
            reclamo_id=reclamo_id,
            usuario_id=current_user.id,
            datos_comentario=datos_comentario
        )
        
        # Crear evento de auditoría
        await EventoAuditoriaService.crear_evento(
            db,
            reclamo_id=reclamo_id,
            tipo_evento="comment_added",
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area,
            descripcion=f"Comentario {'interno' if datos_comentario.es_interno else 'público'} agregado"
        )
        await db.commit()
        
        return comentario
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/comentarios/{comentario_id}", response_model=ComentarioReclamoRespuesta)
async def actualizar_comentario(
    comentario_id: UUID,
    datos_comentario: ComentarioReclamoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Actualizar comentario.
    
    Solo el autor del comentario puede editarlo.
    
    Requiere autenticación.
    """
    try:
        # Verificar que el comentario existe
        comentario_existente = await ComentarioReclamoService.get_by_id(db, comentario_id)
        if not comentario_existente:
            raise ComentarioReclamoNotFoundException(comentario_id)
        
        # Verificar que el usuario es el autor
        if comentario_existente.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el autor puede editar el comentario"
            )
        
        comentario_actualizado = await ComentarioReclamoService.actualizar(
            db,
            comentario_id,
            datos_comentario
        )
        
        return comentario_actualizado
    except ComentarioReclamoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/comentarios/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_comentario(
    comentario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Eliminar comentario.
    
    Solo el autor del comentario o un administrador pueden eliminarlo.
    
    Requiere autenticación.
    """
    try:
        # Verificar que el comentario existe
        comentario_existente = await ComentarioReclamoService.get_by_id(db, comentario_id)
        if not comentario_existente:
            raise ComentarioReclamoNotFoundException(comentario_id)
        
        # Verificar permisos (autor o admin)
        if comentario_existente.usuario_id != current_user.id and current_user.rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este comentario"
            )
        
        await ComentarioReclamoService.eliminar(db, comentario_id)
        return None
    except ComentarioReclamoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================
# ENDPOINTS DE ADJUNTOS
# ============================================

@router.get("/{reclamo_id}/adjuntos", response_model=List[AdjuntoReclamoRespuesta])
async def listar_adjuntos(
    reclamo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar archivos adjuntos de un reclamo.
    
    Los adjuntos están ordenados por fecha descendente (más recientes primero).
    
    Requiere autenticación.
    """
    try:
        # Verificar que el reclamo existe
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        adjuntos = await AdjuntoReclamoService.get_by_reclamo(db, reclamo_id)
        return adjuntos
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{reclamo_id}/adjuntos", response_model=AdjuntoReclamoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_adjunto(
    reclamo_id: UUID,
    datos_adjunto: AdjuntoReclamoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Registrar archivo adjunto a un reclamo.
    
    NOTA: Este endpoint registra la metadata del archivo en la base de datos.
    El upload real del archivo debe manejarse por separado (ej: Supabase Storage).
    
    Requiere autenticación.
    """
    try:
        adjunto = await AdjuntoReclamoService.crear(
            db,
            reclamo_id=reclamo_id,
            usuario_id=current_user.id,
            datos_adjunto=datos_adjunto
        )
        
        # Crear evento de auditoría
        await EventoAuditoriaService.crear_evento(
            db,
            reclamo_id=reclamo_id,
            tipo_evento="attachment_added",
            usuario_id=current_user.id,
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area,
            descripcion=f"Archivo adjunto: {datos_adjunto.nombre_archivo}"
        )
        await db.commit()
        
        return adjunto
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/adjuntos/{adjunto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_adjunto(
    adjunto_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Eliminar archivo adjunto.
    
    Solo el autor del adjunto o un administrador pueden eliminarlo.
    
    NOTA: Este endpoint elimina la metadata de la base de datos.
    El archivo real debe eliminarse por separado (ej: Supabase Storage).
    
    Requiere autenticación.
    """
    try:
        # Verificar que el adjunto existe
        adjunto_existente = await AdjuntoReclamoService.get_by_id(db, adjunto_id)
        if not adjunto_existente:
            raise AdjuntoReclamoNotFoundException(adjunto_id)
        
        # Verificar permisos (autor o admin)
        if adjunto_existente.subido_por != current_user.id and current_user.rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este adjunto"
            )
        
        await AdjuntoReclamoService.eliminar(db, adjunto_id)
        return None
    except AdjuntoReclamoNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
