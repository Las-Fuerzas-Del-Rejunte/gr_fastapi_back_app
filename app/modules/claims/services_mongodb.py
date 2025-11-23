"""
Servicios de Reclamos - Lógica de negocio para MongoDB
SIMPLIFICADO para migración inicial
"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from bson import ObjectId

from app.modules.claims.models_mongodb import (
    Reclamo,
    ConfiguracionEstado,
)
from app.modules.claims.models_complementarios_mongodb import Cliente
from app.modules.users.models_mongodb import Usuario
from app.modules.claims.schemas_mongodb import (
    ReclamoCrear,
    ReclamoActualizar,
)
from app.core.exceptions import ClaimNotFoundException, UserNotFoundException, NotFoundException


# ============================================
# Servicio de Reclamos
# ============================================

class ClaimService:
    """Servicio para operaciones de reclamos"""
    
    @staticmethod
    async def get_all(
        status: Optional[str] = None,
        assigned_to: Optional[str | ObjectId] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "creado_en",
        sort_order: str = "desc"
    ) -> Tuple[List[Reclamo], int]:
        """
        Obtener lista de reclamos con filtros y paginación
        
        Returns:
            Tupla (lista de reclamos, total de resultados)
        """
        # Construir filtros
        filtros = {}
        
        if assigned_to:
            asignado_id = ObjectId(assigned_to) if isinstance(assigned_to, str) else assigned_to
            filtros["asignado_a"] = asignado_id
        
        if priority:
            filtros["prioridad"] = priority
        
        if search:
            # Búsqueda en asunto o nombre de cliente
            filtros["$or"] = [
                {"asunto": {"$regex": search, "$options": "i"}},
                {"nombre_cliente": {"$regex": search, "$options": "i"}}
            ]
        
        # Query base
        query = Reclamo.find(filtros)
        
        # Ordenamiento inteligente compuesto
        # Para reclamos resueltos (que tienen resuelto_en), usar esa fecha
        # Para reclamos no resueltos, usar creado_en
        sort_direction = "-" if sort_order == "desc" else "+"
        
        if sort_by == "creado_en":
            # Ordenar primero por resuelto_en (si existe), luego por creado_en
            # Los reclamos resueltos aparecen primero ordenados por fecha de resolución
            # Los no resueltos aparecen después ordenados por fecha de creación
            query = query.sort([
                (f"{sort_direction}resuelto_en"),
                (f"{sort_direction}{sort_by}")
            ])
        else:
            # Para otros campos, ordenar normalmente
            query = query.sort(f"{sort_direction}{sort_by}")
        
        # Contar total
        total = await query.count()
        
        # Paginación
        reclamos = await query.skip(skip).limit(limit).to_list()
        
        return reclamos, total
    
    @staticmethod
    async def get_by_id(reclamo_id: str | ObjectId) -> Optional[Reclamo]:
        """Obtener reclamo por ID"""
        if isinstance(reclamo_id, str):
            reclamo_id = ObjectId(reclamo_id)
        
        return await Reclamo.get(reclamo_id)
    
    @staticmethod
    async def create_reclamo(reclamo_data: ReclamoCrear, usuario_creador_id: str | ObjectId) -> Reclamo:
        """
        Crear un nuevo reclamo
        
        Args:
            reclamo_data: Datos del reclamo
            usuario_creador_id: ID del usuario que crea el reclamo
            
        Returns:
            Reclamo creado
            
        Raises:
            NotFoundException: Si el estado no existe
        """
        from app.modules.claims.models_mongodb import EventoAuditoriaEmbebido
        from app.modules.users.models_mongodb import Usuario
        
        # Obtener estado inicial o el especificado
        if reclamo_data.estado_id:
            try:
                estado = await ConfiguracionEstado.get(ObjectId(reclamo_data.estado_id))
            except Exception:
                estado = await ConfiguracionEstado.find_one(ConfiguracionEstado.nombre == reclamo_data.estado_id)
        else:
            estado = await ConfiguracionEstado.find_one(ConfiguracionEstado.posicion_orden == 1)
        
        if not estado:
            raise NotFoundException("No se encontró estado configurado")
        
        # Convertir proyecto_id si existe
        proyecto_oid = None
        if reclamo_data.proyecto_id:
            try:
                proyecto_oid = ObjectId(reclamo_data.proyecto_id)
            except Exception:
                pass
        
        # Obtener usuario creador para auditoría
        usuario = await Usuario.get(ObjectId(usuario_creador_id) if isinstance(usuario_creador_id, str) else usuario_creador_id)
        
        # Crear reclamo
        nuevo_reclamo = Reclamo(
            asunto=reclamo_data.asunto,
            nombre_cliente=reclamo_data.nombre_cliente,
            info_contacto=reclamo_data.info_contacto,
            email_cliente=reclamo_data.email_cliente,
            telefono_cliente=reclamo_data.telefono_cliente,
            descripcion=reclamo_data.descripcion,
            categoria=reclamo_data.categoria,
            estado_id=estado.id,
            prioridad=reclamo_data.prioridad,
            proyecto_id=proyecto_oid,
            creado_por=ObjectId(usuario_creador_id) if isinstance(usuario_creador_id, str) else usuario_creador_id,
        )
        
        # Crear evento de auditoría de creación
        if usuario:
            evento = EventoAuditoriaEmbebido(
                tipo_evento="creacion",
                usuario_id=ObjectId(usuario_creador_id) if isinstance(usuario_creador_id, str) else usuario_creador_id,
                nombre_usuario=usuario.nombre,
                area_usuario=usuario.area if hasattr(usuario, 'area') else None,
                cambios=None,
                descripcion=f"Reclamo creado por {usuario.nombre}",
                creado_en=datetime.utcnow()
            )
            nuevo_reclamo.eventos_auditoria = [evento]
        
        await nuevo_reclamo.insert()
        return nuevo_reclamo
    
    @staticmethod
    async def update_reclamo(
        reclamo_id: str | ObjectId,
        reclamo_data: ReclamoActualizar,
        usuario_id: str | ObjectId
    ) -> Reclamo:
        """
        Actualizar un reclamo y crear eventos de auditoría para cambios importantes
        
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        from app.modules.claims.models_mongodb import EventoAuditoriaEmbebido
        from app.modules.users.models_mongodb import Usuario
        
        reclamo = await ClaimService.get_by_id(reclamo_id)
        if not reclamo:
            raise ClaimNotFoundException(f"Reclamo con ID {reclamo_id} no encontrado")
        
        # Obtener usuario que hace el cambio
        usuario = await Usuario.get(ObjectId(usuario_id) if isinstance(usuario_id, str) else usuario_id)
        
        # Actualizar campos y rastrear cambios importantes
        update_data = reclamo_data.model_dump(exclude_unset=True)
        cambios_importantes = []
        
        print(f"🔄 Actualizando reclamo {reclamo_id}")
        print(f"   Datos recibidos: {update_data}")
        
        # Variable para rastrear si cambió asignado_a
        asignado_a_cambio = False
        nuevo_agente = None
        
        for field, value in update_data.items():
            valor_anterior = getattr(reclamo, field, None)
            
            # Convertir strings a ObjectId para campos de referencia
            if field in ['estado_id', 'sub_estado_id', 'asignado_a', 'proyecto_id'] and value:
                if isinstance(value, str):
                    try:
                        value = ObjectId(value)
                        print(f"   ✅ Convertido {field}: {value}")
                    except Exception as e:
                        print(f"   ❌ Error convirtiendo {field}: {e}")
                        
                        # Si no es un ObjectId válido, intentar buscar por nombre (solo para estado_id)
                        if field == 'estado_id':
                            estado = await ConfiguracionEstado.find_one({"nombre": value})
                            if estado:
                                value = estado.id
                                print(f"   🔄 Convertido nombre '{update_data[field]}' a ObjectId: {value}")
                            else:
                                print(f"   ❌ Estado '{value}' no encontrado")
                                raise ValueError(f"Estado '{value}' no encontrado")
                        elif field == 'sub_estado_id':
                            from app.modules.claims.models_mongodb import SubEstado
                            sub_estado = await SubEstado.find_one({"nombre": value})
                            if sub_estado:
                                value = sub_estado.id
                                print(f"   🔄 Convertido nombre sub-estado '{update_data[field]}' a ObjectId: {value}")
                            else:
                                print(f"   ❌ Sub-estado '{value}' no encontrado")
                                raise ValueError(f"Sub-estado '{value}' no encontrado")
                        else:
                            # Para otros campos, el error es válido
                            raise
            
            # Detectar cambio en asignado_a para actualizar asignado_info
            if field == 'asignado_a':
                anterior_str = str(valor_anterior) if valor_anterior else None
                nuevo_str = str(value) if value else None
                if anterior_str != nuevo_str:
                    asignado_a_cambio = True
                    if value:
                        # Cargar el nuevo agente para actualizar asignado_info
                        nuevo_agente = await Usuario.get(value)
                        print(f"   🔄 Cambio de asignación detectado: {anterior_str} → {nuevo_str}")
            
            # Rastrear cambios en campos importantes
            if field in ['estado_id', 'sub_estado_id', 'prioridad']:
                # Comparar correctamente (ambos como strings para comparación)
                anterior_str = str(valor_anterior) if valor_anterior else None
                nuevo_str = str(value) if value else None
                
                if anterior_str != nuevo_str:
                    cambios_importantes.append({
                        "campo": field,
                        "valor_anterior": anterior_str,
                        "valor_nuevo": nuevo_str
                    })
                    print(f"   📝 Cambio detectado en {field}: {anterior_str} → {nuevo_str}")
                    
                    # Si cambió el estado, verificar si es un estado final para actualizar resuelto_en
                    if field == 'estado_id' and value:
                        estado_obj = await ConfiguracionEstado.get(value)
                        if estado_obj and estado_obj.nombre.lower() in ["resuelto", "cerrado", "finalizado", "completado"]:
                            # Establecer fecha de resolución si no existe
                            if not reclamo.resuelto_en:
                                reclamo.resuelto_en = datetime.utcnow()
                                print(f"   ✅ resuelto_en establecido: {reclamo.resuelto_en}")
                        else:
                            # Si se movió fuera de un estado final, limpiar resuelto_en
                            if reclamo.resuelto_en:
                                reclamo.resuelto_en = None
                                print(f"   🔄 resuelto_en limpiado (movido fuera de estado final)")
            
            setattr(reclamo, field, value)
        
        # Actualizar asignado_info si cambió asignado_a
        if asignado_a_cambio:
            if nuevo_agente:
                reclamo.asignado_info = {
                    "nombre": nuevo_agente.nombre,
                    "email": nuevo_agente.email,
                    "area": nuevo_agente.area if hasattr(nuevo_agente, 'area') else None,
                }
                print(f"   ✅ asignado_info actualizado: {reclamo.asignado_info}")
            else:
                reclamo.asignado_info = None
                print(f"   ✅ asignado_info limpiado (desasignación)")
        
        # Crear eventos de auditoría para cambios importantes
        if cambios_importantes and usuario:
            for cambio in cambios_importantes:
                evento = EventoAuditoriaEmbebido(
                    tipo_evento="actualizacion",
                    usuario_id=ObjectId(usuario_id) if isinstance(usuario_id, str) else usuario_id,
                    nombre_usuario=usuario.nombre,
                    area_usuario=usuario.area if hasattr(usuario, 'area') else None,
                    cambios=cambio,
                    descripcion=f"Campo '{cambio['campo']}' actualizado",
                    creado_en=datetime.utcnow()
                )
                
                if not reclamo.eventos_auditoria:
                    reclamo.eventos_auditoria = []
                reclamo.eventos_auditoria.append(evento)
        
        reclamo.actualizado_en = datetime.utcnow()
        await reclamo.save()
        
        return reclamo
    
    @staticmethod
    async def delete_reclamo(reclamo_id: str | ObjectId, usuario_id: str | ObjectId) -> bool:
        """
        Eliminar un reclamo (soft delete)
        
        Raises:
            ClaimNotFoundException: Si el reclamo no existe
        """
        reclamo = await ClaimService.get_by_id(reclamo_id)
        if not reclamo:
            raise ClaimNotFoundException(f"Reclamo con ID {reclamo_id} no encontrado")
        
        # TODO: Implementar soft delete
        await reclamo.delete()
        
        return True

