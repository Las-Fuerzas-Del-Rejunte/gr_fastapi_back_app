"""
Servicios de Status Config, SubEstado y TransicionEstado - Lógica de negocio
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.status.models import StatusConfig, SubEstado, TransicionEstado
from app.modules.status.schemas import (
    ConfigEstadoCrear, 
    ConfigEstadoActualizar,
    SubEstadoCrear,
    SubEstadoActualizar,
    TransicionEstadoCrear,
    TransicionEstadoActualizar
)
from app.core.exceptions import NotFoundException, DuplicateException


class StatusNotFoundException(NotFoundException):
    """Excepción cuando no se encuentra una configuración de estado"""
    def __init__(self, status_id: UUID):
        super().__init__(f"Configuración de estado {status_id} no encontrada")


class StatusConfigService:
    """Servicio para operaciones de configuración de estados"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: UUID) -> Optional[StatusConfig]:
        """Obtener configuración por ID"""
        result = await db.execute(
            select(StatusConfig).where(StatusConfig.id == config_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name(db: AsyncSession, nombre: str) -> Optional[StatusConfig]:
        """Obtener configuración por nombre"""
        result = await db.execute(
            select(StatusConfig).where(StatusConfig.nombre == nombre)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[StatusConfig]:
        """Obtener todas las configuraciones ordenadas por posición"""
        result = await db.execute(
            select(StatusConfig).order_by(StatusConfig.posicion_orden.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create_status_config(db: AsyncSession, datos_configuracion: ConfigEstadoCrear) -> StatusConfig:
        """
        Crear nueva configuración de estado
        
        Args:
            db: Sesión de base de datos
            datos_configuracion: Datos de la configuración
            
        Returns:
            Configuración creada
            
        Raises:
            DuplicateException: Si el nombre ya existe
        """
        # Verificar que el nombre no exista
        existing_config = await StatusConfigService.get_by_name(db, datos_configuracion.nombre)
        if existing_config:
            raise DuplicateException(f"Ya existe una configuración con el nombre '{datos_configuracion.nombre}'")
        
        datos_dict = datos_configuracion.model_dump(exclude_unset=True)
        
        db_configuracion = StatusConfig(**datos_dict)
        
        db.add(db_configuracion)
        await db.commit()
        await db.refresh(db_configuracion)
        
        return db_configuracion
    
    @staticmethod
    async def create(db: AsyncSession, datos_configuracion: ConfigEstadoCrear) -> StatusConfig:
        """Crear nueva configuración de estado (método legacy)"""
        datos_dict = datos_configuracion.model_dump(exclude_unset=True)
        
        db_configuracion = StatusConfig(**datos_dict)
        
        db.add(db_configuracion)
        await db.flush()
        await db.refresh(db_configuracion)
        
        return db_configuracion
    
    @staticmethod
    async def update_status_config(db: AsyncSession, config_id: UUID, datos_configuracion: ConfigEstadoActualizar) -> StatusConfig:
        """
        Actualizar configuración de estado
        
        Args:
            db: Sesión de base de datos
            config_id: ID de la configuración
            datos_configuracion: Datos a actualizar
            
        Returns:
            Configuración actualizada
            
        Raises:
            StatusNotFoundException: Si la configuración no existe
            DuplicateException: Si el nombre ya existe
        """
        db_configuracion = await StatusConfigService.get_by_id(db, config_id)
        
        if not db_configuracion:
            raise StatusNotFoundException(config_id)
        
        datos_actualizacion = datos_configuracion.model_dump(exclude_unset=True)
        
        # Verificar nombre duplicado si se está actualizando
        if 'nombre' in datos_actualizacion and datos_actualizacion['nombre'] != db_configuracion.nombre:
            existing_config = await StatusConfigService.get_by_name(db, datos_actualizacion['nombre'])
            if existing_config:
                raise DuplicateException(f"Ya existe una configuración con el nombre '{datos_actualizacion['nombre']}'")
        
        for campo, valor in datos_actualizacion.items():
            setattr(db_configuracion, campo, valor)
        
        await db.commit()
        await db.refresh(db_configuracion)
        
        return db_configuracion
    
    @staticmethod
    async def update(
        db: AsyncSession,
        configuracion: StatusConfig,
        datos_configuracion: ConfigEstadoActualizar
    ) -> StatusConfig:
        """Actualizar configuración existente (método legacy)"""
        datos_actualizacion = datos_configuracion.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(configuracion, campo, valor)
        
        await db.flush()
        await db.refresh(configuracion)
        
        return configuracion
    
    @staticmethod
    async def delete_status_config(db: AsyncSession, config_id: UUID) -> None:
        """
        Eliminar configuración de estado
        
        Args:
            db: Sesión de base de datos
            config_id: ID de la configuración
            
        Raises:
            StatusNotFoundException: Si la configuración no existe
        """
        db_configuracion = await StatusConfigService.get_by_id(db, config_id)
        
        if not db_configuracion:
            raise StatusNotFoundException(config_id)
        
        await db.delete(db_configuracion)
        await db.commit()
    
    @staticmethod
    async def delete(db: AsyncSession, config: StatusConfig) -> None:
        """Eliminar configuración (método legacy)"""
        await db.delete(config)
        await db.flush()


# ============================================
# SubEstado Service
# ============================================

class SubEstadoNotFoundException(NotFoundException):
    """Excepción cuando no se encuentra un sub-estado"""
    def __init__(self, sub_estado_id: UUID):
        super().__init__(f"Sub-estado {sub_estado_id} no encontrado")


class SubEstadoService:
    """Servicio para operaciones de sub-estados"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, sub_estado_id: UUID, load_relations: bool = False) -> Optional[SubEstado]:
        """
        Obtener sub-estado por ID
        
        Args:
            db: Sesión de base de datos
            sub_estado_id: ID del sub-estado
            load_relations: Si cargar relaciones (estado_padre)
        """
        query = select(SubEstado).where(SubEstado.id == sub_estado_id)
        
        if load_relations:
            query = query.options(selectinload(SubEstado.estado_padre))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession, estado_id: Optional[UUID] = None) -> List[SubEstado]:
        """
        Obtener todos los sub-estados, opcionalmente filtrados por estado
        
        Args:
            db: Sesión de base de datos
            estado_id: ID del estado para filtrar (opcional)
        """
        query = select(SubEstado).options(selectinload(SubEstado.estado_padre))
        
        if estado_id:
            query = query.where(SubEstado.estado_id == estado_id)
        
        query = query.order_by(SubEstado.posicion_orden.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_estado(db: AsyncSession, estado_id: UUID) -> List[SubEstado]:
        """
        Obtener sub-estados de un estado específico
        
        Args:
            db: Sesión de base de datos
            estado_id: ID del estado padre
        """
        return await SubEstadoService.get_all(db, estado_id=estado_id)
    
    @staticmethod
    async def create(db: AsyncSession, datos_sub_estado: SubEstadoCrear) -> SubEstado:
        """
        Crear nuevo sub-estado
        
        Args:
            db: Sesión de base de datos
            datos_sub_estado: Datos del sub-estado
            
        Returns:
            Sub-estado creado
            
        Raises:
            StatusNotFoundException: Si el estado padre no existe
        """
        # Verificar que el estado padre existe
        estado = await StatusConfigService.get_by_id(db, datos_sub_estado.estado_id)
        if not estado:
            raise StatusNotFoundException(datos_sub_estado.estado_id)
        
        datos_dict = datos_sub_estado.model_dump(exclude_unset=True)
        
        db_sub_estado = SubEstado(**datos_dict)
        
        db.add(db_sub_estado)
        await db.commit()
        await db.refresh(db_sub_estado)
        
        return db_sub_estado
    
    @staticmethod
    async def update(db: AsyncSession, sub_estado_id: UUID, datos_sub_estado: SubEstadoActualizar) -> SubEstado:
        """
        Actualizar sub-estado
        
        Args:
            db: Sesión de base de datos
            sub_estado_id: ID del sub-estado
            datos_sub_estado: Datos a actualizar
            
        Returns:
            Sub-estado actualizado
            
        Raises:
            SubEstadoNotFoundException: Si el sub-estado no existe
        """
        db_sub_estado = await SubEstadoService.get_by_id(db, sub_estado_id)
        
        if not db_sub_estado:
            raise SubEstadoNotFoundException(sub_estado_id)
        
        datos_actualizacion = datos_sub_estado.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(db_sub_estado, campo, valor)
        
        await db.commit()
        await db.refresh(db_sub_estado)
        
        return db_sub_estado
    
    @staticmethod
    async def delete(db: AsyncSession, sub_estado_id: UUID) -> None:
        """
        Eliminar sub-estado
        
        Args:
            db: Sesión de base de datos
            sub_estado_id: ID del sub-estado
            
        Raises:
            SubEstadoNotFoundException: Si el sub-estado no existe
        """
        db_sub_estado = await SubEstadoService.get_by_id(db, sub_estado_id)
        
        if not db_sub_estado:
            raise SubEstadoNotFoundException(sub_estado_id)
        
        await db.delete(db_sub_estado)
        await db.commit()


# ============================================
# TransicionEstado Service
# ============================================

class TransicionEstadoNotFoundException(NotFoundException):
    """Excepción cuando no se encuentra una transición de estado"""
    def __init__(self, transicion_id: UUID):
        super().__init__(f"Transición de estado {transicion_id} no encontrada")


class TransicionEstadoService:
    """Servicio para operaciones de transiciones de estado"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, transicion_id: UUID, load_relations: bool = False) -> Optional[TransicionEstado]:
        """
        Obtener transición por ID
        
        Args:
            db: Sesión de base de datos
            transicion_id: ID de la transición
            load_relations: Si cargar relaciones (estados origen/destino)
        """
        query = select(TransicionEstado).where(TransicionEstado.id == transicion_id)
        
        if load_relations:
            query = query.options(
                selectinload(TransicionEstado.estado_origen),
                selectinload(TransicionEstado.estado_destino)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all(db: AsyncSession, load_relations: bool = True) -> List[TransicionEstado]:
        """
        Obtener todas las transiciones
        
        Args:
            db: Sesión de base de datos
            load_relations: Si cargar relaciones (estados)
        """
        query = select(TransicionEstado)
        
        if load_relations:
            query = query.options(
                selectinload(TransicionEstado.estado_origen),
                selectinload(TransicionEstado.estado_destino)
            )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_transiciones_desde_estado(db: AsyncSession, desde_estado_id: UUID) -> List[TransicionEstado]:
        """
        Obtener transiciones válidas desde un estado específico
        
        Args:
            db: Sesión de base de datos
            desde_estado_id: ID del estado origen
            
        Returns:
            Lista de transiciones posibles desde ese estado
        """
        query = (
            select(TransicionEstado)
            .where(TransicionEstado.desde_estado == desde_estado_id)
            .options(
                selectinload(TransicionEstado.estado_origen),
                selectinload(TransicionEstado.estado_destino)
            )
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def validar_transicion(
        db: AsyncSession, 
        desde_estado_id: UUID, 
        hacia_estado_id: UUID,
        rol_usuario: str
    ) -> Optional[TransicionEstado]:
        """
        Validar si una transición es válida y el usuario tiene permisos
        
        Args:
            db: Sesión de base de datos
            desde_estado_id: ID del estado actual
            hacia_estado_id: ID del estado destino
            rol_usuario: Rol del usuario que intenta la transición
            
        Returns:
            La transición si es válida, None si no
        """
        query = (
            select(TransicionEstado)
            .where(
                TransicionEstado.desde_estado == desde_estado_id,
                TransicionEstado.hacia_estado == hacia_estado_id
            )
        )
        
        result = await db.execute(query)
        transicion = result.scalar_one_or_none()
        
        if not transicion:
            return None
        
        # Verificar si el rol del usuario está en los roles requeridos
        if rol_usuario not in transicion.roles_requeridos:
            return None
        
        return transicion
    
    @staticmethod
    async def create(db: AsyncSession, datos_transicion: TransicionEstadoCrear) -> TransicionEstado:
        """
        Crear nueva transición de estado
        
        Args:
            db: Sesión de base de datos
            datos_transicion: Datos de la transición
            
        Returns:
            Transición creada
            
        Raises:
            StatusNotFoundException: Si alguno de los estados no existe
            DuplicateException: Si la transición ya existe
        """
        # Verificar que ambos estados existen
        estado_origen = await StatusConfigService.get_by_id(db, datos_transicion.desde_estado)
        if not estado_origen:
            raise StatusNotFoundException(datos_transicion.desde_estado)
        
        estado_destino = await StatusConfigService.get_by_id(db, datos_transicion.hacia_estado)
        if not estado_destino:
            raise StatusNotFoundException(datos_transicion.hacia_estado)
        
        # Verificar que no exista ya esta transición
        existing = await db.execute(
            select(TransicionEstado).where(
                TransicionEstado.desde_estado == datos_transicion.desde_estado,
                TransicionEstado.hacia_estado == datos_transicion.hacia_estado
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateException(
                f"Ya existe una transición desde '{estado_origen.nombre}' hacia '{estado_destino.nombre}'"
            )
        
        datos_dict = datos_transicion.model_dump(exclude_unset=True)
        
        db_transicion = TransicionEstado(**datos_dict)
        
        db.add(db_transicion)
        await db.commit()
        await db.refresh(db_transicion)
        
        return db_transicion
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        transicion_id: UUID, 
        datos_transicion: TransicionEstadoActualizar
    ) -> TransicionEstado:
        """
        Actualizar transición de estado
        
        Args:
            db: Sesión de base de datos
            transicion_id: ID de la transición
            datos_transicion: Datos a actualizar
            
        Returns:
            Transición actualizada
            
        Raises:
            TransicionEstadoNotFoundException: Si la transición no existe
        """
        db_transicion = await TransicionEstadoService.get_by_id(db, transicion_id)
        
        if not db_transicion:
            raise TransicionEstadoNotFoundException(transicion_id)
        
        datos_actualizacion = datos_transicion.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(db_transicion, campo, valor)
        
        await db.commit()
        await db.refresh(db_transicion)
        
        return db_transicion
    
    @staticmethod
    async def delete(db: AsyncSession, transicion_id: UUID) -> None:
        """
        Eliminar transición de estado
        
        Args:
            db: Sesión de base de datos
            transicion_id: ID de la transición
            
        Raises:
            TransicionEstadoNotFoundException: Si la transición no existe
        """
        db_transicion = await TransicionEstadoService.get_by_id(db, transicion_id)
        
        if not db_transicion:
            raise TransicionEstadoNotFoundException(transicion_id)
        
        await db.delete(db_transicion)
        await db.commit()
