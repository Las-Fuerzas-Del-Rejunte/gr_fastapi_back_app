"""
Servicios de Auditoría - Sistema de Gestión de Reclamos
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.claims.models import AuditEvent
from app.modules.users.models import User
from app.core.schemas import AuditEventCreate


async def create_audit_event(
    db: AsyncSession,
    claim_id: UUID,
    event_type: str,
    user: User,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
) -> AuditEvent:
    """
    Crear evento de auditoría para un reclamo
    
    Args:
        db: Sesión de base de datos async
        claim_id: ID del reclamo
        event_type: Tipo de evento (created, status_changed, assigned, etc.)
        user: Usuario que realiza la acción
        changes: Diccionario con cambios realizados
        description: Descripción del evento
    
    Returns:
        AuditEvent creado
    """
    audit_event = AuditEvent(
        claim_id=str(claim_id),
        event_type=event_type,
        user_id=user.id,
        user_name=user.name,
        user_area=user.area,
        changes=changes,
        description=description
    )
    
    db.add(audit_event)
    await db.commit()
    await db.refresh(audit_event)
    
    return audit_event


async def get_claim_audit_history(
    db: AsyncSession,
    claim_id: UUID
) -> list[AuditEvent]:
    """
    Obtener historial de auditoría de un reclamo
    
    Args:
        db: Sesión de base de datos async
        claim_id: ID del reclamo
    
    Returns:
        Lista de eventos de auditoría ordenados por fecha
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.claim_id == str(claim_id))
        .order_by(AuditEvent.created_at.desc())
    )
    
    return result.scalars().all()
