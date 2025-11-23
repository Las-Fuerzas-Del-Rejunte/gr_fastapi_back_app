"""
Servicios de Reclamos, Comentarios, Adjuntos y Eventos - Lógica de negocio
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.claims.models import (
    Claim, 
    ClaimPriority, 
    EventoAuditoria, 
    ComentarioReclamo, 
    AdjuntoReclamo
)
from app.modules.claims.schemas import (
    ReclamoCrear, 
    ReclamoActualizar,
    ComentarioReclamoCrear,
    ComentarioReclamoActualizar,
    AdjuntoReclamoCrear
)
from app.modules.status.models import StatusConfig
from app.core.exceptions import ClaimNotFoundException, UserNotFoundException, NotFoundException


class ClaimService:
    """Servicio para operaciones de reclamos"""
    
    @staticmethod
    async def _resolver_estado_id(db: AsyncSession, estado_id) -> UUID:
        """
        Resolver estado_id: si es string (nombre), buscar el UUID; si es UUID, retornarlo
        
        Args:
            db: Sesión de base de datos
            estado_id: Puede ser UUID o nombre del estado (str)
            
        Returns:
            UUID del estado
            
        Raises:
            NotFoundException: Si el estado no existe
        """
        # Si ya es UUID, retornar directamente
        if isinstance(estado_id, UUID):
            return estado_id
        
        # Si es string, intentar parsear como UUID primero
        if isinstance(estado_id, str):
            try:
                return UUID(estado_id)
            except ValueError:
                # No es UUID válido, buscar por nombre (case-insensitive)
                result = await db.execute(
                    select(StatusConfig.id).where(func.lower(StatusConfig.nombre) == estado_id.lower())
                )
                estado_uuid = result.scalar_one_or_none()
                
                if not estado_uuid:
                    raise NotFoundException(f"Estado '{estado_id}' no encontrado")
                
                return estado_uuid
        
        raise ValueError(f"estado_id debe ser UUID o string, recibido: {type(estado_id)}")
    
    @staticmethod
    async def _resolver_sub_estado_id(db: AsyncSession, sub_estado_id) -> UUID:
        """
        Resolver sub_estado_id: si es string (nombre), buscar el UUID; si es UUID, retornarlo
        
        Args:
            db: Sesión de base de datos
            sub_estado_id: Puede ser UUID o nombre del sub-estado (str)
            
        Returns:
            UUID del sub-estado
            
        Raises:
            NotFoundException: Si el sub-estado no existe
        """
        # Si ya es UUID, retornar directamente
        if isinstance(sub_estado_id, UUID):
            return sub_estado_id
        
        # Si es string, intentar parsear como UUID primero
        if isinstance(sub_estado_id, str):
            try:
                return UUID(sub_estado_id)
            except ValueError:
                # No es UUID válido, buscar por nombre (case-insensitive)
                from app.modules.status.models import SubEstado
                result = await db.execute(
                    select(SubEstado.id).where(func.lower(SubEstado.nombre) == sub_estado_id.lower())
                )
                sub_estado_uuid = result.scalar_one_or_none()
                
                if not sub_estado_uuid:
                    raise NotFoundException(f"Sub-estado '{sub_estado_id}' no encontrado")
                
                return sub_estado_uuid
        
        raise ValueError(f"sub_estado_id debe ser UUID o string, recibido: {type(sub_estado_id)}")
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        claim_id: UUID,
        load_relations: bool = True
    ) -> Optional[Claim]:
        """Obtener reclamo por ID"""
        query = select(Claim).where(Claim.id == claim_id)
        
        if load_relations:
            query = query.options(
                selectinload(Claim.agente_asignado),
                selectinload(Claim.comentarios)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        priority: Optional[ClaimPriority] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Claim], int]:
        """
        Obtener lista de reclamos con filtros y paginación
        
        Returns:
            Tupla de (lista de reclamos, total count)
        """
        # Query base con eager loading de relaciones básicas (sin comentarios/adjuntos para rendimiento)
        query = select(Claim).options(
            selectinload(Claim.agente_asignado),
            selectinload(Claim.estado_config),
            selectinload(Claim.sub_estado_config)
        )
        count_query = select(func.count()).select_from(Claim)
        
        # Filtros
        filters = []
        
        if status:
            # status puede ser UUID (estado_id) o nombre del estado
            try:
                # Intentar parsear como UUID
                estado_uuid = UUID(status) if isinstance(status, str) else status
                filters.append(Claim.estado_id == estado_uuid)
            except (ValueError, TypeError):
                # Si falla, buscar por nombre del estado usando JOIN
                from app.modules.status.models import StatusConfig
                query = query.join(StatusConfig, Claim.estado_id == StatusConfig.id)
                count_query = count_query.join(StatusConfig, Claim.estado_id == StatusConfig.id)
                filters.append(StatusConfig.nombre == status)
        
        if assigned_to:
            filters.append(Claim.asignado_a == assigned_to)
        
        if priority:
            filters.append(Claim.prioridad == priority)
        
        if search:
            search_filter = or_(
                Claim.asunto.ilike(f"%{search}%"),
                Claim.nombre_cliente.ilike(f"%{search}%"),
                Claim.descripcion.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
        
        # Ordenamiento
        sort_column = getattr(Claim, sort_by, Claim.creado_en)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        # Ejecutar queries
        result = await db.execute(query)
        claims = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return list(claims), total
    
    @staticmethod
    async def create_claim(db: AsyncSession, datos_reclamo: ReclamoCrear) -> Claim:
        """
        Crear nuevo reclamo
        
        Args:
            db: Sesión de base de datos
            datos_reclamo: Datos del reclamo
            
        Returns:
            Reclamo creado
            
        Raises:
            UserNotFoundException: Si el agente asignado no existe
        """
        datos_dict = datos_reclamo.model_dump(exclude_unset=True)
        
        # Resolver estado_id si es nombre de estado
        if 'estado_id' in datos_dict:
            datos_dict['estado_id'] = await ClaimService._resolver_estado_id(
                db, datos_dict['estado_id']
            )
        
        # Validar que el agente existe si se proporciona
        if datos_dict.get('asignado_a'):
            from app.modules.users.services import UserService
            agente = await UserService.get_by_id(db, datos_dict['asignado_a'])
            if not agente:
                raise UserNotFoundException(f"Agente {datos_dict['asignado_a']} no encontrado")
        
        db_reclamo = Claim(**datos_dict)
        
        db.add(db_reclamo)
        await db.commit()
        await db.refresh(db_reclamo, ["agente_asignado", "estado_config", "sub_estado_config"])
        
        return db_reclamo
    
    @staticmethod
    async def create(db: AsyncSession, datos_reclamo: ReclamoCrear) -> Claim:
        """Crear nuevo reclamo (método legacy)"""
        datos_dict = datos_reclamo.model_dump(exclude_unset=True)
        
        # Resolver estado_id si es nombre de estado
        if 'estado_id' in datos_dict:
            datos_dict['estado_id'] = await ClaimService._resolver_estado_id(
                db, datos_dict['estado_id']
            )
        
        db_reclamo = Claim(**datos_dict)
        
        db.add(db_reclamo)
        await db.flush()
        await db.refresh(db_reclamo, ["agente_asignado", "estado_config", "sub_estado_config"])
        
        return db_reclamo
    
    @staticmethod
    async def update_claim(db: AsyncSession, reclamo_id: UUID, datos_actualizacion: ReclamoActualizar) -> Claim:
        """
        Actualizar reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            datos_actualizacion: Datos a actualizar
            
        Returns:
            Reclamo actualizado
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
            UserNotFoundException: Si el agente asignado no existe
        """
        result = await db.execute(select(Claim).where(Claim.id == reclamo_id))
        db_reclamo = result.scalars().first()
        
        if not db_reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        datos_dict = datos_actualizacion.model_dump(exclude_unset=True)
        
        # Resolver estado_id si se proporciona como nombre
        if 'estado_id' in datos_dict and datos_dict['estado_id']:
            datos_dict['estado_id'] = await ClaimService._resolver_estado_id(
                db, datos_dict['estado_id']
            )
        
        # Resolver sub_estado_id si se proporciona como nombre
        if 'sub_estado_id' in datos_dict and datos_dict['sub_estado_id']:
            datos_dict['sub_estado_id'] = await ClaimService._resolver_sub_estado_id(
                db, datos_dict['sub_estado_id']
            )
        
        # Validar que el agente existe si se proporciona
        if 'asignado_a' in datos_dict and datos_dict['asignado_a']:
            from app.modules.users.services import UserService
            agente = await UserService.get_by_id(db, datos_dict['asignado_a'])
            if not agente:
                raise UserNotFoundException(f"Agente {datos_dict['asignado_a']} no encontrado")
        
        for key, value in datos_dict.items():
            setattr(db_reclamo, key, value)
        
        db_reclamo.fecha_actualizacion = datetime.now(timezone.utc)
        
        await db.commit()
        # Solo cargar relaciones básicas para mejor rendimiento
        await db.refresh(db_reclamo, [
            "agente_asignado", 
            "estado_config", 
            "sub_estado_config"
        ])
        
        return db_reclamo
    
    @staticmethod
    async def update(
        db: AsyncSession,
        reclamo: Claim,
        datos_reclamo: ReclamoActualizar
    ) -> Claim:
        """Actualizar reclamo existente (método legacy)"""
        datos_actualizacion = datos_reclamo.model_dump(exclude_unset=True)
        
        # Resolver estado_id si es nombre de estado
        if 'estado_id' in datos_actualizacion and datos_actualizacion['estado_id']:
            datos_actualizacion['estado_id'] = await ClaimService._resolver_estado_id(
                db, datos_actualizacion['estado_id']
            )
        
        for campo, valor in datos_actualizacion.items():
            setattr(reclamo, campo, valor)
        
        await db.flush()
        # Solo cargar relaciones básicas para mejor rendimiento
        await db.refresh(reclamo, [
            "agente_asignado", 
            "estado_config",
            "sub_estado_config"
        ])
        
        return reclamo
    
    @staticmethod
    async def assign_agent_to_claim(db: AsyncSession, reclamo_id: UUID, agente_id: Optional[UUID]) -> Claim:
        """
        Asignar o desasignar agente a un reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            agente_id: ID del agente a asignar (None para desasignar)
            
        Returns:
            Reclamo actualizado
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
            UserNotFoundException: Si el agente no existe
        """
        result = await db.execute(select(Claim).where(Claim.id == reclamo_id))
        db_reclamo = result.scalars().first()
        
        if not db_reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        # Validar que el agente existe si se proporciona
        if agente_id:
            from app.modules.users.services import UserService
            agente = await UserService.get_by_id(db, agente_id)
            if not agente:
                raise UserNotFoundException(f"Agente {agente_id} no encontrado")
        
        db_reclamo.asignado_a = agente_id
        db_reclamo.fecha_actualizacion = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(
            db_reclamo, 
            [
                "agente_asignado",
                "estado_config",
                "sub_estado_config",
                "proyecto",
                "comentarios",
                "adjuntos"
            ]
        )
        
        return db_reclamo
    
    @staticmethod
    async def assign_agent(
        db: AsyncSession,
        reclamo: Claim,
        agente_id: Optional[UUID]
    ) -> Claim:
        """Asignar o desasignar agente a un reclamo (método legacy)"""
        reclamo.asignado_a = agente_id
        
        await db.flush()
        await db.refresh(reclamo, ["agente_asignado"])
        
        return reclamo
    
    @staticmethod
    async def delete_claim(db: AsyncSession, reclamo_id: UUID) -> None:
        """
        Eliminar reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        result = await db.execute(select(Claim).where(Claim.id == reclamo_id))
        db_reclamo = result.scalars().first()
        
        if not db_reclamo:
            raise ClaimNotFoundException(reclamo_id)
        
        await db.delete(db_reclamo)
        await db.commit()
    
    @staticmethod
    async def delete(db: AsyncSession, claim: Claim) -> None:
        """Eliminar reclamo (método legacy)"""
        await db.delete(claim)
        await db.flush()


# ============================================
# EventoAuditoria Service
# ============================================

class EventoAuditoriaService:
    """Servicio para operaciones de eventos de auditoría"""
    
    @staticmethod
    async def crear_evento(
        db: AsyncSession,
        reclamo_id: UUID,
        tipo_evento: str,
        usuario_id: Optional[UUID],
        nombre_usuario: str,
        area_usuario: Optional[str] = None,
        cambios: Optional[Dict[str, Any]] = None,
        descripcion: Optional[str] = None
    ) -> EventoAuditoria:
        """
        Crear evento de auditoría
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            tipo_evento: Tipo de evento (created, status_changed, assigned, etc.)
            usuario_id: ID del usuario (puede ser None para eventos del sistema)
            nombre_usuario: Nombre del usuario
            area_usuario: Área del usuario
            cambios: Diccionario con detalles de los cambios
            descripcion: Descripción del evento
            
        Returns:
            Evento creado
        """
        db_evento = EventoAuditoria(
            reclamo_id=reclamo_id,
            tipo_evento=tipo_evento,
            usuario_id=usuario_id,
            nombre_usuario=nombre_usuario,
            area_usuario=area_usuario,
            cambios=cambios,
            descripcion=descripcion
        )
        
        db.add(db_evento)
        await db.flush()
        await db.refresh(db_evento)
        
        return db_evento
    
    @staticmethod
    async def get_by_reclamo(
        db: AsyncSession,
        reclamo_id: UUID,
        limite: Optional[int] = None
    ) -> List[EventoAuditoria]:
        """
        Obtener eventos de auditoría de un reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            limite: Cantidad máxima de eventos a retornar (None = todos)
            
        Returns:
            Lista de eventos ordenados por fecha descendente
        """
        query = (
            select(EventoAuditoria)
            .where(EventoAuditoria.reclamo_id == reclamo_id)
            .order_by(EventoAuditoria.creado_en.desc())
        )
        
        if limite:
            query = query.limit(limite)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# ============================================
# ComentarioReclamo Service
# ============================================

class ComentarioReclamoNotFoundException(NotFoundException):
    """Excepción cuando no se encuentra un comentario"""
    def __init__(self, comentario_id: UUID):
        super().__init__(f"Comentario {comentario_id} no encontrado")


class ComentarioReclamoService:
    """Servicio para operaciones de comentarios"""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        comentario_id: UUID,
        load_relations: bool = True
    ) -> Optional[ComentarioReclamo]:
        """Obtener comentario por ID"""
        query = select(ComentarioReclamo).where(ComentarioReclamo.id == comentario_id)
        
        if load_relations:
            query = query.options(selectinload(ComentarioReclamo.usuario))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_reclamo(
        db: AsyncSession,
        reclamo_id: UUID,
        incluir_internos: bool = True
    ) -> List[ComentarioReclamo]:
        """
        Obtener comentarios de un reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            incluir_internos: Si incluir comentarios internos
            
        Returns:
            Lista de comentarios ordenados por fecha descendente
        """
        query = (
            select(ComentarioReclamo)
            .where(ComentarioReclamo.reclamo_id == reclamo_id)
            .options(selectinload(ComentarioReclamo.usuario))
        )
        
        if not incluir_internos:
            query = query.where(ComentarioReclamo.es_interno == False)
        
        query = query.order_by(ComentarioReclamo.creado_en.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def crear(
        db: AsyncSession,
        reclamo_id: UUID,
        usuario_id: UUID,
        datos_comentario: ComentarioReclamoCrear
    ) -> ComentarioReclamo:
        """
        Crear comentario en reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            usuario_id: ID del usuario que crea el comentario
            datos_comentario: Datos del comentario
            
        Returns:
            Comentario creado
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        # Verificar que el reclamo existe
        reclamo = await db.execute(select(Claim).where(Claim.id == reclamo_id))
        if not reclamo.scalar_one_or_none():
            raise ClaimNotFoundException(reclamo_id)
        
        datos_dict = datos_comentario.model_dump(exclude_unset=True)
        datos_dict['reclamo_id'] = reclamo_id
        datos_dict['usuario_id'] = usuario_id
        
        db_comentario = ComentarioReclamo(**datos_dict)
        
        db.add(db_comentario)
        await db.commit()
        await db.refresh(db_comentario)
        
        # Cargar relación usuario
        await db.refresh(db_comentario, ["usuario"])
        
        return db_comentario
    
    @staticmethod
    async def actualizar(
        db: AsyncSession,
        comentario_id: UUID,
        datos_comentario: ComentarioReclamoActualizar
    ) -> ComentarioReclamo:
        """
        Actualizar comentario
        
        Args:
            db: Sesión de base de datos
            comentario_id: ID del comentario
            datos_comentario: Datos a actualizar
            
        Returns:
            Comentario actualizado
            
        Raises:
            ComentarioReclamoNotFoundException: Si el comentario no existe
        """
        db_comentario = await ComentarioReclamoService.get_by_id(db, comentario_id)
        
        if not db_comentario:
            raise ComentarioReclamoNotFoundException(comentario_id)
        
        datos_actualizacion = datos_comentario.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(db_comentario, campo, valor)
        
        await db.commit()
        await db.refresh(db_comentario)
        
        return db_comentario
    
    @staticmethod
    async def eliminar(db: AsyncSession, comentario_id: UUID) -> None:
        """
        Eliminar comentario
        
        Args:
            db: Sesión de base de datos
            comentario_id: ID del comentario
            
        Raises:
            ComentarioReclamoNotFoundException: Si el comentario no existe
        """
        db_comentario = await ComentarioReclamoService.get_by_id(db, comentario_id)
        
        if not db_comentario:
            raise ComentarioReclamoNotFoundException(comentario_id)
        
        await db.delete(db_comentario)
        await db.commit()


# ============================================
# AdjuntoReclamo Service
# ============================================

class AdjuntoReclamoNotFoundException(NotFoundException):
    """Excepción cuando no se encuentra un adjunto"""
    def __init__(self, adjunto_id: UUID):
        super().__init__(f"Adjunto {adjunto_id} no encontrado")


class AdjuntoReclamoService:
    """Servicio para operaciones de adjuntos"""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        adjunto_id: UUID,
        load_relations: bool = True
    ) -> Optional[AdjuntoReclamo]:
        """Obtener adjunto por ID"""
        query = select(AdjuntoReclamo).where(AdjuntoReclamo.id == adjunto_id)
        
        if load_relations:
            query = query.options(selectinload(AdjuntoReclamo.usuario))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_reclamo(db: AsyncSession, reclamo_id: UUID) -> List[AdjuntoReclamo]:
        """
        Obtener adjuntos de un reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            
        Returns:
            Lista de adjuntos ordenados por fecha descendente
        """
        query = (
            select(AdjuntoReclamo)
            .where(AdjuntoReclamo.reclamo_id == reclamo_id)
            .options(selectinload(AdjuntoReclamo.usuario))
            .order_by(AdjuntoReclamo.creado_en.desc())
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def crear(
        db: AsyncSession,
        reclamo_id: UUID,
        usuario_id: UUID,
        datos_adjunto: AdjuntoReclamoCrear
    ) -> AdjuntoReclamo:
        """
        Crear adjunto en reclamo
        
        Args:
            db: Sesión de base de datos
            reclamo_id: ID del reclamo
            usuario_id: ID del usuario que sube el archivo
            datos_adjunto: Datos del adjunto
            
        Returns:
            Adjunto creado
            
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        # Verificar que el reclamo existe
        reclamo = await db.execute(select(Claim).where(Claim.id == reclamo_id))
        if not reclamo.scalar_one_or_none():
            raise ClaimNotFoundException(reclamo_id)
        
        datos_dict = datos_adjunto.model_dump(exclude_unset=True)
        datos_dict['reclamo_id'] = reclamo_id
        datos_dict['subido_por'] = usuario_id
        
        db_adjunto = AdjuntoReclamo(**datos_dict)
        
        db.add(db_adjunto)
        await db.commit()
        await db.refresh(db_adjunto)
        
        # Cargar relación usuario
        await db.refresh(db_adjunto, ["usuario"])
        
        return db_adjunto
    
    @staticmethod
    async def eliminar(db: AsyncSession, adjunto_id: UUID) -> None:
        """
        Eliminar adjunto
        
        Args:
            db: Sesión de base de datos
            adjunto_id: ID del adjunto
            
        Raises:
            AdjuntoReclamoNotFoundException: Si el adjunto no existe
        """
        db_adjunto = await AdjuntoReclamoService.get_by_id(db, adjunto_id)
        
        if not db_adjunto:
            raise AdjuntoReclamoNotFoundException(adjunto_id)
        
        await db.delete(db_adjunto)
        await db.commit()
