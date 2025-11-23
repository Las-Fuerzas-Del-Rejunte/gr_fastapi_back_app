"""
Servicios de Clientes y Proyectos
"""
from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.clients.models import Cliente, TipoProyecto, Proyecto
from app.core.exceptions import NotFoundException


class ClienteService:
    """Servicio para operaciones de Cliente"""
    
    @staticmethod
    async def crear(db: AsyncSession, cliente_data: dict) -> Cliente:
        """Crear un nuevo cliente"""
        cliente = Cliente(**cliente_data)
        db.add(cliente)
        await db.commit()
        await db.refresh(cliente)
        return cliente
    
    @staticmethod
    async def obtener_por_id(db: AsyncSession, cliente_id: uuid.UUID) -> Optional[Cliente]:
        """Obtener cliente por ID"""
        result = await db.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def obtener_por_correo(db: AsyncSession, correo: str) -> Optional[Cliente]:
        """Obtener cliente por correo"""
        result = await db.execute(
            select(Cliente).where(Cliente.correo == correo)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def listar(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True
    ) -> List[Cliente]:
        """Listar clientes con paginación"""
        query = select(Cliente)
        
        if solo_activos:
            query = query.where(Cliente.activo == True)
        
        query = query.offset(skip).limit(limit).order_by(Cliente.apellido, Cliente.nombre)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def actualizar(
        db: AsyncSession,
        cliente_id: uuid.UUID,
        cliente_data: dict
    ) -> Optional[Cliente]:
        """Actualizar cliente"""
        cliente = await ClienteService.obtener_por_id(db, cliente_id)
        if not cliente:
            return None
        
        for key, value in cliente_data.items():
            if value is not None:
                setattr(cliente, key, value)
        
        await db.commit()
        await db.refresh(cliente)
        return cliente
    
    @staticmethod
    async def eliminar(db: AsyncSession, cliente_id: uuid.UUID) -> bool:
        """Eliminar (desactivar) cliente"""
        cliente = await ClienteService.obtener_por_id(db, cliente_id)
        if not cliente:
            return False
        
        cliente.activo = False
        await db.commit()
        return True


class TipoProyectoService:
    """Servicio para operaciones de Tipo de Proyecto"""
    
    @staticmethod
    async def crear(db: AsyncSession, tipo_data: dict) -> TipoProyecto:
        """Crear un nuevo tipo de proyecto"""
        tipo = TipoProyecto(**tipo_data)
        db.add(tipo)
        await db.commit()
        await db.refresh(tipo)
        return tipo
    
    @staticmethod
    async def obtener_por_id(db: AsyncSession, tipo_id: uuid.UUID) -> Optional[TipoProyecto]:
        """Obtener tipo de proyecto por ID"""
        result = await db.execute(
            select(TipoProyecto).where(TipoProyecto.id == tipo_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def listar(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True
    ) -> List[TipoProyecto]:
        """Listar tipos de proyecto"""
        query = select(TipoProyecto)
        
        if solo_activos:
            query = query.where(TipoProyecto.activo == True)
        
        query = query.offset(skip).limit(limit).order_by(TipoProyecto.descripcion)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def actualizar(
        db: AsyncSession,
        tipo_id: uuid.UUID,
        tipo_data: dict
    ) -> Optional[TipoProyecto]:
        """Actualizar tipo de proyecto"""
        tipo = await TipoProyectoService.obtener_por_id(db, tipo_id)
        if not tipo:
            return None
        
        for key, value in tipo_data.items():
            if value is not None:
                setattr(tipo, key, value)
        
        await db.commit()
        await db.refresh(tipo)
        return tipo


class ProyectoService:
    """Servicio para operaciones de Proyecto"""
    
    @staticmethod
    async def crear(db: AsyncSession, proyecto_data: dict) -> Proyecto:
        """Crear un nuevo proyecto"""
        proyecto = Proyecto(**proyecto_data)
        db.add(proyecto)
        await db.commit()
        await db.refresh(proyecto, ["cliente", "tipo_proyecto"])
        return proyecto
    
    @staticmethod
    async def obtener_por_id(db: AsyncSession, proyecto_id: uuid.UUID) -> Optional[Proyecto]:
        """Obtener proyecto por ID con relaciones cargadas"""
        result = await db.execute(
            select(Proyecto)
            .options(selectinload(Proyecto.cliente))
            .options(selectinload(Proyecto.tipo_proyecto))
            .where(Proyecto.id == proyecto_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def listar(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True
    ) -> List[Proyecto]:
        """Listar proyectos con relaciones cargadas"""
        query = select(Proyecto).options(
            selectinload(Proyecto.cliente),
            selectinload(Proyecto.tipo_proyecto)
        )
        
        if solo_activos:
            query = query.where(Proyecto.activo == True)
        
        query = query.offset(skip).limit(limit).order_by(Proyecto.nombre)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def listar_por_cliente(
        db: AsyncSession,
        cliente_id: uuid.UUID,
        solo_activos: bool = True
    ) -> List[Proyecto]:
        """Listar proyectos de un cliente específico"""
        query = select(Proyecto).options(
            selectinload(Proyecto.cliente),
            selectinload(Proyecto.tipo_proyecto)
        ).where(Proyecto.cliente_id == cliente_id)
        
        if solo_activos:
            query = query.where(Proyecto.activo == True)
        
        query = query.order_by(Proyecto.nombre)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def listar_por_tipo(
        db: AsyncSession,
        tipo_proyecto_id: uuid.UUID,
        solo_activos: bool = True
    ) -> List[Proyecto]:
        """Listar proyectos por tipo"""
        query = select(Proyecto).options(
            selectinload(Proyecto.cliente),
            selectinload(Proyecto.tipo_proyecto)
        ).where(Proyecto.tipo_proyecto_id == tipo_proyecto_id)
        
        if solo_activos:
            query = query.where(Proyecto.activo == True)
        
        query = query.order_by(Proyecto.nombre)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def actualizar(
        db: AsyncSession,
        proyecto_id: uuid.UUID,
        proyecto_data: dict
    ) -> Optional[Proyecto]:
        """Actualizar proyecto"""
        proyecto = await ProyectoService.obtener_por_id(db, proyecto_id)
        if not proyecto:
            return None
        
        for key, value in proyecto_data.items():
            if value is not None:
                setattr(proyecto, key, value)
        
        await db.commit()
        await db.refresh(proyecto, ["cliente", "tipo_proyecto"])
        return proyecto
    
    @staticmethod
    async def eliminar(db: AsyncSession, proyecto_id: uuid.UUID) -> bool:
        """Eliminar (desactivar) proyecto"""
        proyecto = await ProyectoService.obtener_por_id(db, proyecto_id)
        if not proyecto:
            return False
        
        proyecto.activo = False
        await db.commit()
        return True
