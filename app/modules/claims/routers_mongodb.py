"""
Router de Reclamos - Endpoints de la API para MongoDB
SIMPLIFICADO para migración inicial
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.schemas import PaginatedResponse, PaginationMeta
from app.modules.claims.schemas_mongodb import (
    ReclamoCrear,
    ReclamoRespuesta,
    ReclamoActualizar,
    ReclamoAsignar,
    ReclamoItemLista,
    ReclamoDetalle,
)
from app.modules.claims.services_mongodb import (
    ClaimService,
)
from app.modules.auth.dependencies import get_current_user
from app.core.exceptions import ClaimNotFoundException

router = APIRouter(prefix="/reclamos", tags=["reclamos"])


async def _construir_reclamo_respuesta(reclamo, incluir_detalles: bool = False):
    """
    Helper para construir respuesta de reclamo con estado_config y sub_estado_config completos.
    
    Args:
        reclamo: Documento Reclamo de MongoDB
        incluir_detalles: Si True, incluye comentarios, adjuntos y eventos
    """
    from app.modules.claims.models_mongodb import ConfiguracionEstado, SubEstado
    from bson import ObjectId as BsonObjectId
    
    reclamo_id_str = str(reclamo.id)
    
    # Cargar estado_config
    estado_config = None
    if reclamo.estado_id:
        estado = await ConfiguracionEstado.get(reclamo.estado_id)
        if estado:
            estado_config = {
                "id": str(estado.id),
                "nombre": estado.nombre,
                "color": estado.color,
                "posicion_orden": estado.posicion_orden,
                "descripcion": estado.descripcion,
                "area": estado.area,
            }
        else:
            estado_config = {
                "id": str(reclamo.estado_id),
                "nombre": "Desconocido",
                "color": "#gray",
                "posicion_orden": 999,
            }
    
    # Cargar sub_estado_config
    sub_estado_config = None
    if getattr(reclamo, 'sub_estado_id', None):
        sub = await SubEstado.get(reclamo.sub_estado_id)
        if sub:
            sub_estado_config = {
                "id": str(sub.id),
                "nombre": sub.nombre,
                "descripcion": sub.descripcion,
                "posicion_orden": sub.posicion_orden,
            }
        else:
            sub_estado_config = {
                "id": str(reclamo.sub_estado_id),
                "nombre": "Desconocido",
                "posicion_orden": 999,
            }
    
    # Construir agente_asignado
    agente_asignado = None
    if reclamo.asignado_a:
        # Intentar usar información desnormalizada primero
        if reclamo.asignado_info:
            agente_asignado = {
                "id": str(reclamo.asignado_a),
                "nombre": reclamo.asignado_info.get("nombre"),
                "email": reclamo.asignado_info.get("email"),
                "area": reclamo.asignado_info.get("area"),
            }
        else:
            # Si no hay info desnormalizada, cargar del usuario
            from app.modules.users.models_mongodb import Usuario
            try:
                usuario = await Usuario.get(reclamo.asignado_a)
                if usuario:
                    agente_asignado = {
                        "id": str(usuario.id),
                        "nombre": usuario.nombre,
                        "email": usuario.email,
                        "area": usuario.area if hasattr(usuario, 'area') else None,
                    }
            except Exception:
                pass
    
    reclamo_dict = {
        "id": reclamo_id_str,
        "numero_reclamo": reclamo_id_str[-8:].upper(),
        "asunto": reclamo.asunto,
        "nombre_cliente": reclamo.nombre_cliente,
        "info_contacto": reclamo.info_contacto if hasattr(reclamo, 'info_contacto') else None,
        "descripcion": reclamo.descripcion if hasattr(reclamo, 'descripcion') else None,
        "estado_id": str(reclamo.estado_id) if reclamo.estado_id else None,
        "prioridad": reclamo.prioridad,
        "sub_estado_id": str(reclamo.sub_estado_id) if reclamo.sub_estado_id else None,
        "categoria": reclamo.categoria if hasattr(reclamo, 'categoria') else None,
        "email_cliente": reclamo.email_cliente if hasattr(reclamo, 'email_cliente') else None,
        "telefono_cliente": reclamo.telefono_cliente if hasattr(reclamo, 'telefono_cliente') else None,
        "proyecto_id": str(reclamo.proyecto_id) if reclamo.proyecto_id else None,
        "resumen_resolucion": reclamo.resumen_resolucion if hasattr(reclamo, 'resumen_resolucion') else None,
        "bloqueado": reclamo.bloqueado if hasattr(reclamo, 'bloqueado') else False,
        "resuelto_en": reclamo.resuelto_en.isoformat() if hasattr(reclamo, 'resuelto_en') and reclamo.resuelto_en else None,
        "creado_en": reclamo.creado_en.isoformat() if reclamo.creado_en else None,
        "actualizado_en": reclamo.actualizado_en.isoformat() if reclamo.actualizado_en else None,
        "asignado_a": str(reclamo.asignado_a) if reclamo.asignado_a else None,
        # Objetos anidados
        "estado_config": estado_config,
        "sub_estado_config": sub_estado_config,
        "agente_asignado": agente_asignado,
        "cantidad_comentarios": len(reclamo.comentarios) if reclamo.comentarios else 0,
        "cantidad_adjuntos": len(reclamo.adjuntos) if reclamo.adjuntos else 0,
    }
    
    # Si es detalle, incluir comentarios, adjuntos y eventos
    if incluir_detalles:
        # Comentarios
        comentarios = []
        if reclamo.comentarios:
            for com in reclamo.comentarios:
                comentarios.append({
                    "id": str(com.id),
                    "contenido": com.contenido,
                    "usuario_id": str(com.usuario_id) if com.usuario_id else None,
                    "usuario_nombre": com.usuario_nombre,
                    "usuario_area": com.usuario_area,
                    "creado_en": com.creado_en.isoformat() if com.creado_en else None,
                    "actualizado_en": com.actualizado_en.isoformat() if com.actualizado_en else None,
                })
        
        # Adjuntos
        adjuntos = []
        if reclamo.adjuntos:
            for adj in reclamo.adjuntos:
                adjuntos.append({
                    "id": str(adj.id),
                    "nombre_archivo": adj.nombre_archivo,
                    "tipo_mime": adj.tipo_mime,
                    "tamano": adj.tamano,
                    "url": adj.url,
                    "subido_por": str(adj.subido_por) if adj.subido_por else None,
                    "subido_por_nombre": adj.subido_por_nombre,
                    "creado_en": adj.creado_en.isoformat() if adj.creado_en else None,
                })
        
        # Eventos recientes (últimos 10)
        eventos_recientes = []
        if reclamo.eventos_auditoria:
            for ev in reclamo.eventos_auditoria[-10:]:
                eventos_recientes.append({
                    "id": str(ev.id),
                    "tipo_evento": ev.tipo_evento,
                    "nombre_usuario": ev.nombre_usuario,
                    "area_usuario": ev.area_usuario,
                    "cambios": ev.cambios,
                    "descripcion": ev.descripcion,
                    "creado_en": ev.creado_en.isoformat() if ev.creado_en else None,
                })
        
        reclamo_dict["comentarios"] = comentarios
        reclamo_dict["adjuntos"] = adjuntos
        reclamo_dict["eventos_recientes"] = eventos_recientes
    
    return reclamo_dict


@router.get("")
async def listar_reclamos(
    estado: Optional[str] = Query(None, description="Filtrar por estado (nombre)"),
    asignado_a: Optional[str] = Query(None, description="Filtrar por agente asignado (ID)"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    buscar: Optional[str] = Query(None, description="Buscar en asunto y nombre de cliente"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    limite: int = Query(20, ge=1, le=100, description="Items por página"),
    ordenar_por: str = Query("creado_en", description="Campo para ordenar"),
    orden: str = Query("desc", pattern="^(asc|desc)$", description="Orden"),
    current_user = Depends(get_current_user),
):
    """
    Listar todos los reclamos con filtros y paginación.
    
    Requiere autenticación.
    """
    skip = (pagina - 1) * limite
    
    reclamos, total = await ClaimService.get_all(
        status=estado,
        assigned_to=asignado_a,
        priority=prioridad,
        search=buscar,
        skip=skip,
        limit=limite,
        sort_by=ordenar_por,
        sort_order=orden,
    )
    
    # Convertir a schemas de respuesta - con carga masiva optimizada
    reclamos_respuesta = []
    
    # Obtener todos los IDs únicos para hacer queries en lote
    estado_ids = list(set([str(r.estado_id) for r in reclamos if r.estado_id]))
    sub_estado_ids = list(set([str(r.sub_estado_id) for r in reclamos if getattr(r, 'sub_estado_id', None)]))
    usuario_ids = list(set([str(r.asignado_a) for r in reclamos if r.asignado_a and not r.asignado_info]))
    
    # Cargar todos los estados, sub-estados y usuarios de una sola vez
    from app.modules.claims.models_mongodb import ConfiguracionEstado, SubEstado
    from app.modules.users.models_mongodb import Usuario
    from bson import ObjectId as BsonObjectId
    
    estados_dict = {}
    sub_estados_dict = {}
    usuarios_dict = {}
    
    if estado_ids:
        estado_object_ids = [BsonObjectId(eid) for eid in estado_ids]
        estados = await ConfiguracionEstado.find({"_id": {"$in": estado_object_ids}}).to_list()
        estados_dict = {str(e.id): e for e in estados}
    
    if sub_estado_ids:
        sub_object_ids = [BsonObjectId(sid) for sid in sub_estado_ids]
        sub_estados = await SubEstado.find({"_id": {"$in": sub_object_ids}}).to_list()
        sub_estados_dict = {str(s.id): s for s in sub_estados}
    
    if usuario_ids:
        usuario_object_ids = [BsonObjectId(uid) for uid in usuario_ids]
        usuarios = await Usuario.find({"_id": {"$in": usuario_object_ids}}).to_list()
        usuarios_dict = {str(u.id): u for u in usuarios}
    
    # Construir respuesta para cada reclamo
    for reclamo in reclamos:
        reclamo_id_str = str(reclamo.id)
        
        # Construir estado_config
        estado_config = None
        if reclamo.estado_id:
            estado_id_str = str(reclamo.estado_id)
            estado = estados_dict.get(estado_id_str)
            if estado:
                estado_config = {
                    "id": estado_id_str,
                    "nombre": estado.nombre,
                    "color": estado.color,
                    "posicion_orden": estado.posicion_orden,
                    "descripcion": estado.descripcion,
                    "area": estado.area,
                }
            else:
                estado_config = {
                    "id": estado_id_str,
                    "nombre": "Desconocido",
                    "color": "#gray",
                    "posicion_orden": 999,
                }
        
        # Construir sub_estado_config
        sub_estado_config = None
        if getattr(reclamo, 'sub_estado_id', None):
            sub_id_str = str(reclamo.sub_estado_id)
            sub = sub_estados_dict.get(sub_id_str)
            if sub:
                sub_estado_config = {
                    "id": sub_id_str,
                    "nombre": sub.nombre,
                    "descripcion": sub.descripcion,
                    "posicion_orden": sub.posicion_orden,
                }
            else:
                sub_estado_config = {
                    "id": sub_id_str,
                    "nombre": "Desconocido",
                    "posicion_orden": 999,
                }
        
        # Construir agente_asignado
        agente_asignado = None
        if reclamo.asignado_a:
            if reclamo.asignado_info:
                # Usar datos desnormalizados
                agente_asignado = {
                    "id": str(reclamo.asignado_a),
                    "nombre": reclamo.asignado_info.get("nombre"),
                    "email": reclamo.asignado_info.get("email"),
                    "area": reclamo.asignado_info.get("area"),
                }
            else:
                # Fallback: cargar desde diccionario pre-cargado
                usuario_id_str = str(reclamo.asignado_a)
                usuario = usuarios_dict.get(usuario_id_str)
                if usuario:
                    agente_asignado = {
                        "id": usuario_id_str,
                        "nombre": usuario.nombre,
                        "email": usuario.email,
                        "area": usuario.area,
                    }
        
        reclamo_dict = {
            "id": reclamo_id_str,
            "numero_reclamo": reclamo_id_str[-8:].upper(),
            "asunto": reclamo.asunto,
            "nombre_cliente": reclamo.nombre_cliente,
            "info_contacto": reclamo.info_contacto if hasattr(reclamo, 'info_contacto') else None,
            "descripcion": reclamo.descripcion if hasattr(reclamo, 'descripcion') else None,
            "estado_id": str(reclamo.estado_id) if reclamo.estado_id else None,
            "prioridad": reclamo.prioridad,
            "sub_estado_id": str(reclamo.sub_estado_id) if reclamo.sub_estado_id else None,
            "categoria": reclamo.categoria if hasattr(reclamo, 'categoria') else None,
            "email_cliente": reclamo.email_cliente if hasattr(reclamo, 'email_cliente') else None,
            "telefono_cliente": reclamo.telefono_cliente if hasattr(reclamo, 'telefono_cliente') else None,
            "proyecto_id": str(reclamo.proyecto_id) if reclamo.proyecto_id else None,
            "resumen_resolucion": reclamo.resumen_resolucion if hasattr(reclamo, 'resumen_resolucion') else None,
            "bloqueado": reclamo.bloqueado if hasattr(reclamo, 'bloqueado') else False,
            "resuelto_en": reclamo.resuelto_en.isoformat() if hasattr(reclamo, 'resuelto_en') and reclamo.resuelto_en else None,
            "creado_en": reclamo.creado_en.isoformat() if reclamo.creado_en else None,
            "actualizado_en": reclamo.actualizado_en.isoformat() if reclamo.actualizado_en else None,
            "asignado_a": str(reclamo.asignado_a) if reclamo.asignado_a else None,
            # Objetos anidados
            "estado_config": estado_config,
            "sub_estado_config": sub_estado_config,
            "agente_asignado": agente_asignado,
            "cantidad_comentarios": len(reclamo.comentarios) if reclamo.comentarios else 0,
            "cantidad_adjuntos": len(reclamo.adjuntos) if reclamo.adjuntos else 0,
        }
        reclamos_respuesta.append(reclamo_dict)
    
    # Metadatos de paginación
    total_paginas = (total + limite - 1) // limite
    
    response_data = {
        "datos": reclamos_respuesta,
        "paginacion": {
            "total": total,
            "pagina": pagina,
            "limite": limite,
            "total_paginas": total_paginas
        }
    }
    
    return JSONResponse(content=response_data)


@router.get("/{reclamo_id}")
async def obtener_reclamo(
    reclamo_id: str,
    current_user = Depends(get_current_user),
):
    """
    Obtener un reclamo por ID con detalles completos.
    
    Requiere autenticación.
    """
    reclamo = await ClaimService.get_by_id(reclamo_id)
    
    if not reclamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reclamo con ID {reclamo_id} no encontrado"
        )
    
    reclamo_dict = await _construir_reclamo_respuesta(reclamo, incluir_detalles=True)
    return JSONResponse(content=reclamo_dict)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_reclamo(
    reclamo_data: ReclamoCrear,
    current_user = Depends(get_current_user),
):
    """
    Crear un nuevo reclamo.
    
    Requiere autenticación.
    """
    try:
        reclamo = await ClaimService.create_reclamo(reclamo_data, current_user.id)
        reclamo_dict = await _construir_reclamo_respuesta(reclamo, incluir_detalles=False)
        return JSONResponse(content=reclamo_dict, status_code=status.HTTP_201_CREATED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{reclamo_id}")
async def actualizar_reclamo(
    reclamo_id: str,
    reclamo_data: ReclamoActualizar,
    current_user = Depends(get_current_user),
):
    """
    Actualizar un reclamo.
    
    Requiere autenticación.
    """
    try:
        reclamo = await ClaimService.update_reclamo(reclamo_id, reclamo_data, current_user.id)
        reclamo_dict = await _construir_reclamo_respuesta(reclamo, incluir_detalles=False)
        return JSONResponse(content=reclamo_dict)
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{reclamo_id}/asignar")
async def asignar_reclamo(
    reclamo_id: str,
    datos_asignacion: ReclamoAsignar,
    current_user = Depends(get_current_user),
):
    """
    Asignar o desasignar un reclamo a un agente.
    
    Si agente_id es None, se desasigna el reclamo.
    Requiere autenticación.
    """
    from bson import ObjectId
    from app.modules.claims.models_mongodb import Reclamo, EventoAuditoriaEmbebido
    from app.modules.users.models_mongodb import Usuario
    from datetime import datetime
    
    print(f"📥 DATOS RECIBIDOS EN ASIGNAR: {datos_asignacion.model_dump()}")
    
    try:
        # Obtener el reclamo
        reclamo = await Reclamo.get(ObjectId(reclamo_id))
        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reclamo no encontrado"
            )
        
        # Guardar valor anterior para auditoría
        asignado_anterior = str(reclamo.asignado_a) if reclamo.asignado_a else None
        agente_nombre = None
        
        print(f"🔄 Asignación - Reclamo: {reclamo_id}")
        print(f"   Asignado anterior: {asignado_anterior}")
        print(f"   Nuevo agente_id: {datos_asignacion.agente_id}")
        
        # Asignar o desasignar
        if datos_asignacion.agente_id:
            # Verificar que el agente existe
            agente = await Usuario.get(ObjectId(datos_asignacion.agente_id))
            if not agente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agente no encontrado"
                )
            reclamo.asignado_a = ObjectId(datos_asignacion.agente_id)
            agente_nombre = agente.nombre
            
            # Actualizar info desnormalizada
            reclamo.asignado_info = {
                "nombre": agente.nombre,
                "email": agente.email,
                "area": agente.area if hasattr(agente, 'area') else None,
            }
            print(f"   ✅ Asignado a: {agente_nombre} (ID: {datos_asignacion.agente_id})")
            print(f"   ✅ asignado_info actualizado: {reclamo.asignado_info}")
        else:
            # Desasignar
            reclamo.asignado_a = None
            reclamo.asignado_info = None
            agente_nombre = "sin asignar"
            print(f"   ✅ Desasignado (asignado_a = None)")
        
        # Crear evento de auditoría
        evento = EventoAuditoriaEmbebido(
            tipo_evento="asignacion",
            usuario_id=ObjectId(current_user.id),
            nombre_usuario=current_user.nombre,
            area_usuario=current_user.area if hasattr(current_user, 'area') else None,
            cambios={
                "campo": "asignado_a",
                "valor_anterior": asignado_anterior,
                "valor_nuevo": datos_asignacion.agente_id
            },
            descripcion=f"Reclamo asignado a {agente_nombre}",
            creado_en=datetime.utcnow()
        )
        
        # Agregar evento a la lista de eventos
        if not reclamo.eventos_auditoria:
            reclamo.eventos_auditoria = []
        reclamo.eventos_auditoria.append(evento)
        
        # Guardar cambios
        reclamo.actualizado_en = datetime.utcnow()
        await reclamo.save()
        
        # Devolver respuesta con estructura completa
        reclamo_dict = await _construir_reclamo_respuesta(reclamo, incluir_detalles=False)
        return JSONResponse(content=reclamo_dict)
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID inválido"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{reclamo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_reclamo(
    reclamo_id: str,
    current_user = Depends(get_current_user),
):
    """
    Eliminar un reclamo (soft delete).
    
    Requiere autenticación.
    """
    try:
        await ClaimService.delete_reclamo(reclamo_id, current_user.id)
        return None
    except ClaimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{reclamo_id}/auditoria")
async def listar_eventos_auditoria(
    reclamo_id: str,
    limite: Optional[int] = Query(None, ge=1, le=100, description="Cantidad máxima de eventos"),
    current_user = Depends(get_current_user),
):
    """
    Obtener historial de eventos de auditoría de un reclamo.
    
    Los eventos están ordenados por fecha descendente (más recientes primero).
    En MongoDB, los eventos están embebidos en el documento del reclamo.
    
    Requiere autenticación.
    """
    from bson import ObjectId
    from app.modules.claims.models_mongodb import Reclamo
    from datetime import datetime
    
    try:
        # Obtener el reclamo
        reclamo = await Reclamo.get(ObjectId(reclamo_id))
        if not reclamo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reclamo no encontrado"
            )
        
        # Obtener eventos de auditoría embebidos
        eventos = reclamo.eventos_auditoria if hasattr(reclamo, 'eventos_auditoria') else []
        
        # Ordenar por fecha descendente (más recientes primero)
        eventos_ordenados = sorted(
            eventos, 
            key=lambda e: e.creado_en if hasattr(e, 'creado_en') else datetime.min,
            reverse=True
        )
        
        # Aplicar límite si se especifica
        if limite:
            eventos_ordenados = eventos_ordenados[:limite]
        
        # Serializar eventos
        eventos_serializados = []
        for evento in eventos_ordenados:
            evento_dict = {
                "id": str(evento.id) if hasattr(evento, 'id') else None,
                "tipo_evento": evento.tipo_evento if hasattr(evento, 'tipo_evento') else None,
                "usuario_id": str(evento.usuario_id) if hasattr(evento, 'usuario_id') and evento.usuario_id else None,
                "nombre_usuario": evento.nombre_usuario if hasattr(evento, 'nombre_usuario') else None,
                "area_usuario": evento.area_usuario if hasattr(evento, 'area_usuario') else None,
                "cambios": evento.cambios if hasattr(evento, 'cambios') else None,
                "descripcion": evento.descripcion if hasattr(evento, 'descripcion') else None,
                "creado_en": evento.creado_en.isoformat() if hasattr(evento, 'creado_en') and isinstance(evento.creado_en, datetime) else None,
            }
            eventos_serializados.append(evento_dict)
        
        return JSONResponse(content=eventos_serializados)
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID inválido"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
