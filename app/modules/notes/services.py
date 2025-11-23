"""
Servicios de Notas - Lógica de negocio
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notes.models import ClaimNote
from app.modules.notes.schemas import NotaReclamoCrear, NotaReclamoActualizar
from app.core.exceptions import NoteNotFoundException, ClaimNotFoundException


class ClaimNoteService:
    """Servicio para operaciones de notas de reclamos"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, note_id: UUID) -> Optional[ClaimNote]:
        """Obtener nota por ID"""
        result = await db.execute(
            select(ClaimNote).where(ClaimNote.id == note_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_claim(db: AsyncSession, reclamo_id: UUID) -> List[ClaimNote]:
        """Obtener todas las notas de un reclamo"""
        result = await db.execute(
            select(ClaimNote)
            .where(ClaimNote.reclamo_id == reclamo_id)
            .order_by(ClaimNote.creado_en.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create_note_for_claim(
        db: AsyncSession,
        reclamo_id: UUID,
        datos_nota: NotaReclamoCrear,
        autor: str
    ) -> ClaimNote:
        """
        Crear nueva nota para un reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            datos_nota: Datos de la nota
            autor: Nombre del autor (usuario autenticado)
            
        Returns:
            Nota creada
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        # Verificar que el reclamo existe
        from app.modules.claims.services import ClaimService
        reclamo = await ClaimService.get_by_id(db, reclamo_id, load_relations=False)
        if not reclamo:
            raise ClaimNotFoundException(f"Reclamo {reclamo_id} no encontrado")
        
        # Crear nota
        db_nota = ClaimNote(
            reclamo_id=reclamo_id,
            contenido=datos_nota.contenido,
            autor=autor
        )
        
        db.add(db_nota)
        await db.commit()
        await db.refresh(db_nota)
        
        return db_nota
    
    @staticmethod
    async def create(
        db: AsyncSession,
        reclamo_id: UUID,
        datos_nota: NotaReclamoCrear
    ) -> ClaimNote:
        """Crear nueva nota (método legacy)"""
        datos_dict = datos_nota.model_dump(exclude_unset=True)
        datos_dict['reclamo_id'] = reclamo_id
        
        db_nota = ClaimNote(**datos_dict)
        
        db.add(db_nota)
        await db.flush()
        await db.refresh(db_nota)
        
        return db_nota
    
    @staticmethod
    async def update_note(
        db: AsyncSession,
        nota_id: UUID,
        reclamo_id: UUID,
        datos_nota: NotaReclamoActualizar
    ) -> ClaimNote:
        """
        Actualizar nota existente
        
        Args:
            db: Sesión de base de datos
            nota_id: ID de la nota
            reclamo_id: ID del reclamo (para validación)
            datos_nota: Datos a actualizar
            
        Returns:
            Nota actualizada
            
        Raises:
            NoteNotFoundException: Si la nota no existe o no pertenece al reclamo
        """
        nota = await ClaimNoteService.get_by_id(db, nota_id)
        
        if not nota or nota.reclamo_id != reclamo_id:
            raise NoteNotFoundException(f"Nota {nota_id} no encontrada")
        
        datos_actualizacion = datos_nota.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(nota, campo, valor)
        
        await db.commit()
        await db.refresh(nota)
        
        return nota
    
    @staticmethod
    async def delete_note(
        db: AsyncSession,
        nota_id: UUID,
        reclamo_id: UUID
    ) -> None:
        """
        Eliminar nota
        
        Args:
            db: Sesión de base de datos
            nota_id: ID de la nota
            reclamo_id: ID del reclamo (para validación)
            
        Raises:
            NoteNotFoundException: Si la nota no existe o no pertenece al reclamo
        """
        nota = await ClaimNoteService.get_by_id(db, nota_id)
        
        if not nota or nota.reclamo_id != reclamo_id:
            raise NoteNotFoundException(f"Nota {nota_id} no encontrada")
        
        await db.delete(nota)
        await db.commit()
    
    @staticmethod
    async def update(
        db: AsyncSession,
        nota: ClaimNote,
        datos_nota: NotaReclamoActualizar
    ) -> ClaimNote:
        """Actualizar nota existente (método legacy)"""
        datos_actualizacion = datos_nota.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(nota, campo, valor)
        
        await db.flush()
        await db.refresh(nota)
        
        return nota
    
    @staticmethod
    async def delete(db: AsyncSession, note: ClaimNote) -> None:
        """Eliminar nota (método legacy)"""
        await db.delete(note)
        await db.flush()
