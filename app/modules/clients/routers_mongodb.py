"""
Router MongoDB de Clientes, Tipos de Proyecto y Proyectos
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from beanie import PydanticObjectId
from datetime import datetime

from app.modules.auth.dependencies import get_current_user
from app.modules.clients.models_mongodb import Cliente, TipoProyecto, Proyecto
from app.modules.clients.schemas import (
    ClienteCrear,
    ClienteActualizar,
    TipoProyectoCrear,
    TipoProyectoActualizar,
    ProyectoCrear,
    ProyectoActualizar,
)

# Routers
router_clientes = APIRouter(prefix="/clientes", tags=["clientes"])
router_tipos_proyecto = APIRouter(prefix="/tipos-proyecto", tags=["tipos-proyecto"])
router_proyectos = APIRouter(prefix="/proyectos", tags=["proyectos"])


# ============================================
# HELPERS
# ============================================

async def _construir_cliente_respuesta(cliente: Cliente, incluir_proyectos: bool = False) -> dict:
    """
    Construye la respuesta de un cliente con la estructura esperada por el frontend.
    Opcionalmente incluye los proyectos asociados.
    """
    respuesta = {
        "id": str(cliente.id),
        "nombre": cliente.nombre,
        "apellido": cliente.apellido,
        "telefono": cliente.telefono,
        "correo": cliente.correo,
        "empresa": cliente.empresa,
        "activo": cliente.activo,
        "nombre_completo": cliente.nombre_completo,
        "creado_en": cliente.creado_en.isoformat() if isinstance(cliente.creado_en, datetime) else cliente.creado_en,
        "actualizado_en": cliente.actualizado_en.isoformat() if isinstance(cliente.actualizado_en, datetime) else cliente.actualizado_en,
    }
    
    if incluir_proyectos:
        # Cargar proyectos del cliente
        # IMPORTANTE: cliente_id en MongoDB está como ObjectId, no como string
        proyectos = await Proyecto.find(
            Proyecto.cliente_id == cliente.id,
            Proyecto.activo == True
        ).to_list()
        
        # Construir lista de proyectos con información completa
        proyectos_lista = []
        for proyecto in proyectos:
            proyecto_dict = await _construir_proyecto_respuesta(proyecto)
            proyectos_lista.append(proyecto_dict)
        
        respuesta["proyectos"] = proyectos_lista
    
    return respuesta


async def _construir_tipo_proyecto_respuesta(tipo: TipoProyecto) -> dict:
    """Construye la respuesta de un tipo de proyecto"""
    return {
        "id": str(tipo.id),
        "descripcion": tipo.descripcion,
        "activo": tipo.activo,
        "creado_en": tipo.creado_en.isoformat() if isinstance(tipo.creado_en, datetime) else tipo.creado_en,
        "actualizado_en": tipo.actualizado_en.isoformat() if isinstance(tipo.actualizado_en, datetime) else tipo.actualizado_en,
    }


async def _construir_proyecto_respuesta(proyecto: Proyecto) -> dict:
    """Construye la respuesta de un proyecto con información completa del cliente y tipo"""
    # Cargar cliente - ya es PydanticObjectId, no necesita conversión
    cliente = await Cliente.get(proyecto.cliente_id)
    # Cargar tipo de proyecto - ya es PydanticObjectId, no necesita conversión
    tipo_proyecto = await TipoProyecto.get(proyecto.tipo_proyecto_id)
    
    respuesta = {
        "id": str(proyecto.id),
        "nombre": proyecto.nombre,
        "descripcion": proyecto.descripcion,
        "cliente_id": str(proyecto.cliente_id),
        "tipo_proyecto_id": str(proyecto.tipo_proyecto_id),
        "activo": proyecto.activo,
        "creado_en": proyecto.creado_en.isoformat() if isinstance(proyecto.creado_en, datetime) else proyecto.creado_en,
        "actualizado_en": proyecto.actualizado_en.isoformat() if isinstance(proyecto.actualizado_en, datetime) else proyecto.actualizado_en,
    }
    
    # Añadir información del cliente si existe
    if cliente:
        respuesta["cliente"] = await _construir_cliente_respuesta(cliente)
    else:
        respuesta["cliente"] = None
    
    # Añadir información del tipo de proyecto si existe
    if tipo_proyecto:
        respuesta["tipo_proyecto"] = await _construir_tipo_proyecto_respuesta(tipo_proyecto)
    else:
        respuesta["tipo_proyecto"] = None
    
    return respuesta


# ============================================
# ENDPOINTS DE CLIENTES
# ============================================

@router_clientes.get("")
async def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los clientes con sus proyectos"""
    query_filter = {}
    if solo_activos:
        query_filter["activo"] = True
    
    clientes = await Cliente.find(query_filter).skip(skip).limit(limit).to_list()
    
    # Construir respuestas con proyectos
    respuestas = []
    for cliente in clientes:
        cliente_dict = await _construir_cliente_respuesta(cliente, incluir_proyectos=True)
        respuestas.append(cliente_dict)
    
    return JSONResponse(content=respuestas)


@router_clientes.get("/{cliente_id}")
async def obtener_cliente(
    cliente_id: str,
    usuario_actual = Depends(get_current_user),
):
    """Obtener un cliente por ID con sus proyectos"""
    try:
        cliente = await Cliente.get(PydanticObjectId(cliente_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    cliente_dict = await _construir_cliente_respuesta(cliente, incluir_proyectos=True)
    return JSONResponse(content=cliente_dict)


@router_clientes.post("", status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    cliente_data: ClienteCrear,
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo cliente"""
    # Verificar si el correo ya existe
    cliente_existente = await Cliente.find_one(Cliente.correo == cliente_data.correo)
    if cliente_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con ese correo electrónico"
        )
    
    # Crear cliente
    nuevo_cliente = Cliente(**cliente_data.model_dump())
    await nuevo_cliente.insert()
    
    cliente_dict = await _construir_cliente_respuesta(nuevo_cliente)
    return JSONResponse(content=cliente_dict, status_code=status.HTTP_201_CREATED)


@router_clientes.patch("/{cliente_id}")
async def actualizar_cliente(
    cliente_id: str,
    cliente_data: ClienteActualizar,
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un cliente existente"""
    try:
        cliente = await Cliente.get(PydanticObjectId(cliente_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Si se está actualizando el correo, verificar que no exista
    if cliente_data.correo:
        cliente_con_correo = await Cliente.find_one(Cliente.correo == cliente_data.correo)
        if cliente_con_correo and str(cliente_con_correo.id) != cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese correo electrónico"
            )
    
    # Actualizar campos
    update_data = cliente_data.model_dump(exclude_unset=True)
    update_data["actualizado_en"] = datetime.now()
    
    for field, value in update_data.items():
        setattr(cliente, field, value)
    
    await cliente.save()
    
    cliente_dict = await _construir_cliente_respuesta(cliente)
    return JSONResponse(content=cliente_dict)


@router_clientes.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_cliente(
    cliente_id: str,
    usuario_actual = Depends(get_current_user),
):
    """Desactivar un cliente (soft delete)"""
    try:
        cliente = await Cliente.get(PydanticObjectId(cliente_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Soft delete
    cliente.activo = False
    cliente.actualizado_en = datetime.now()
    await cliente.save()
    
    return None


# ============================================
# ENDPOINTS DE TIPOS DE PROYECTO
# ============================================

@router_tipos_proyecto.get("")
async def listar_tipos_proyecto(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los tipos de proyecto"""
    query_filter = {}
    if solo_activos:
        query_filter["activo"] = True
    
    tipos = await TipoProyecto.find(query_filter).skip(skip).limit(limit).to_list()
    
    respuestas = []
    for tipo in tipos:
        tipo_dict = await _construir_tipo_proyecto_respuesta(tipo)
        respuestas.append(tipo_dict)
    
    return JSONResponse(content=respuestas)


@router_tipos_proyecto.get("/{tipo_id}")
async def obtener_tipo_proyecto(
    tipo_id: str,
    usuario_actual = Depends(get_current_user),
):
    """Obtener un tipo de proyecto por ID"""
    try:
        tipo = await TipoProyecto.get(PydanticObjectId(tipo_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    tipo_dict = await _construir_tipo_proyecto_respuesta(tipo)
    return JSONResponse(content=tipo_dict)


@router_tipos_proyecto.post("", status_code=status.HTTP_201_CREATED)
async def crear_tipo_proyecto(
    tipo_data: TipoProyectoCrear,
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo tipo de proyecto"""
    nuevo_tipo = TipoProyecto(**tipo_data.model_dump())
    await nuevo_tipo.insert()
    
    tipo_dict = await _construir_tipo_proyecto_respuesta(nuevo_tipo)
    return JSONResponse(content=tipo_dict, status_code=status.HTTP_201_CREATED)


@router_tipos_proyecto.patch("/{tipo_id}")
async def actualizar_tipo_proyecto(
    tipo_id: str,
    tipo_data: TipoProyectoActualizar,
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un tipo de proyecto existente"""
    try:
        tipo = await TipoProyecto.get(PydanticObjectId(tipo_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    # Actualizar campos
    update_data = tipo_data.model_dump(exclude_unset=True)
    update_data["actualizado_en"] = datetime.now()
    
    for field, value in update_data.items():
        setattr(tipo, field, value)
    
    await tipo.save()
    
    tipo_dict = await _construir_tipo_proyecto_respuesta(tipo)
    return JSONResponse(content=tipo_dict)


# ============================================
# ENDPOINTS DE PROYECTOS
# ============================================

@router_proyectos.get("")
async def listar_proyectos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    solo_activos: bool = Query(True),
    usuario_actual = Depends(get_current_user),
):
    """Listar todos los proyectos"""
    query_filter = {}
    if solo_activos:
        query_filter["activo"] = True
    
    proyectos = await Proyecto.find(query_filter).skip(skip).limit(limit).to_list()
    
    respuestas = []
    for proyecto in proyectos:
        proyecto_dict = await _construir_proyecto_respuesta(proyecto)
        respuestas.append(proyecto_dict)
    
    return JSONResponse(content=respuestas)


@router_proyectos.get("/cliente/{cliente_id}")
async def listar_proyectos_por_cliente(
    cliente_id: str,
    solo_activos: bool = Query(True),
    usuario_actual = Depends(get_current_user),
):
    """Listar proyectos de un cliente específico"""
    # Convertir cliente_id string a PydanticObjectId para la búsqueda
    try:
        cliente_oid = PydanticObjectId(cliente_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cliente inválido"
        )
    
    # Buscar proyectos usando el ObjectId
    query_conditions = [Proyecto.cliente_id == cliente_oid]
    if solo_activos:
        query_conditions.append(Proyecto.activo == True)
    
    proyectos = await Proyecto.find(*query_conditions).to_list()
    
    respuestas = []
    for proyecto in proyectos:
        proyecto_dict = await _construir_proyecto_respuesta(proyecto)
        respuestas.append(proyecto_dict)
    
    return JSONResponse(content=respuestas)


@router_proyectos.get("/{proyecto_id}")
async def obtener_proyecto(
    proyecto_id: str,
    usuario_actual = Depends(get_current_user),
):
    """Obtener un proyecto por ID"""
    try:
        proyecto = await Proyecto.get(PydanticObjectId(proyecto_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    proyecto_dict = await _construir_proyecto_respuesta(proyecto)
    return JSONResponse(content=proyecto_dict)


@router_proyectos.post("", status_code=status.HTTP_201_CREATED)
async def crear_proyecto(
    proyecto_data: ProyectoCrear,
    usuario_actual = Depends(get_current_user),
):
    """Crear un nuevo proyecto"""
    # Verificar que el cliente existe
    try:
        cliente = await Cliente.get(PydanticObjectId(proyecto_data.cliente_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar que el tipo de proyecto existe
    try:
        tipo = await TipoProyecto.get(PydanticObjectId(proyecto_data.tipo_proyecto_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de proyecto no encontrado"
        )
    
    # Crear proyecto - convertir IDs a PydanticObjectId
    proyecto_dict = proyecto_data.model_dump()
    proyecto_dict["cliente_id"] = PydanticObjectId(proyecto_data.cliente_id)
    proyecto_dict["tipo_proyecto_id"] = PydanticObjectId(proyecto_data.tipo_proyecto_id)
    
    nuevo_proyecto = Proyecto(**proyecto_dict)
    await nuevo_proyecto.insert()
    
    proyecto_respuesta = await _construir_proyecto_respuesta(nuevo_proyecto)
    return JSONResponse(content=proyecto_respuesta, status_code=status.HTTP_201_CREATED)


@router_proyectos.patch("/{proyecto_id}")
async def actualizar_proyecto(
    proyecto_id: str,
    proyecto_data: ProyectoActualizar,
    usuario_actual = Depends(get_current_user),
):
    """Actualizar un proyecto existente"""
    try:
        proyecto = await Proyecto.get(PydanticObjectId(proyecto_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    # Actualizar campos
    update_data = proyecto_data.model_dump(exclude_unset=True)
    
    # Convertir IDs a PydanticObjectId si están presentes
    if "cliente_id" in update_data:
        update_data["cliente_id"] = PydanticObjectId(update_data["cliente_id"])
    if "tipo_proyecto_id" in update_data:
        update_data["tipo_proyecto_id"] = PydanticObjectId(update_data["tipo_proyecto_id"])
    
    update_data["actualizado_en"] = datetime.now()
    
    for field, value in update_data.items():
        setattr(proyecto, field, value)
    
    await proyecto.save()
    
    proyecto_dict = await _construir_proyecto_respuesta(proyecto)
    return JSONResponse(content=proyecto_dict)


@router_proyectos.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_proyecto(
    proyecto_id: str,
    usuario_actual = Depends(get_current_user),
):
    """Desactivar un proyecto (soft delete)"""
    try:
        proyecto = await Proyecto.get(PydanticObjectId(proyecto_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    # Soft delete
    proyecto.activo = False
    proyecto.actualizado_en = datetime.now()
    await proyecto.save()
    
    return None
