"""
Router de Notas - Endpoints de la API
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NoteNotFoundException, ClaimNotFoundException
from app.modules.notes.schemas import (
    NotaReclamoCrear,
    NotaReclamoRespuesta,
    NotaReclamoActualizar,
)
from app.modules.notes.services import ClaimNoteService
from app.modules.claims.services import ClaimService
from app.modules.auth.dependencies import get_current_user

router = APIRouter(prefix="/reclamos/{reclamo_id}/notas", tags=["notas"])


@router.get("", response_model=List[NotaReclamoRespuesta])
async def listar_notas(
    reclamo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Listar todas las notas de un reclamo.
    
    Requiere autenticación.
    """
    # Verificar que el reclamo existe
    reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
    if not reclamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reclamo no encontrado"
        )
    
    notas = await ClaimNoteService.get_by_claim(db, reclamo_id)
    return notas


@router.post("", response_model=NotaReclamoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_nota(
    reclamo_id: UUID,
    datos_nota: NotaReclamoCrear,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Crear nueva nota en un reclamo.
    
    Requiere autenticación.
    """
    try:
        nota = await ClaimNoteService.create_note_for_claim(
            db=db,
            reclamo_id=reclamo_id,
            datos_nota=datos_nota,
            autor=current_user.nombre
        )
        return nota
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{nota_id}", response_model=NotaReclamoRespuesta)
async def actualizar_nota(
    reclamo_id: UUID,
    nota_id: UUID,
    datos_nota: NotaReclamoActualizar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Actualizar una nota existente.
    
    Requiere autenticación.
    """
    try:
        nota_actualizada = await ClaimNoteService.update_note(
            db=db,
            nota_id=nota_id,
            reclamo_id=reclamo_id,
            datos_nota=datos_nota
        )
        return nota_actualizada
    except NoteNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{nota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_nota(
    reclamo_id: UUID,
    nota_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Eliminar una nota.
    
    Requiere autenticación.
    """
    try:
        await ClaimNoteService.delete_note(
            db=db,
            nota_id=nota_id,
            reclamo_id=reclamo_id
        )
        return None
    except NoteNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
