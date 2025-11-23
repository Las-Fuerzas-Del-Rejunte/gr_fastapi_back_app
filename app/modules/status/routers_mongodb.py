"""
Router de Configuración de Estados - MongoDB
Versión adaptada para MongoDB/Beanie
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime

from app.modules.claims.models_mongodb import ConfiguracionEstado, SubEstado
from app.modules.auth.dependencies import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/configuracion-estados", tags=["configuracion-estados"])


# ============================================
# Schemas para crear/actualizar
# ============================================

class ConfigEstadoCrear(BaseModel):
    """Schema para crear configuración de estado"""
    nombre: str
    color: str
    posicion_orden: int
    descripcion: Optional[str] = None
    area: Optional[str] = None
    permisos: Optional[dict] = Field(default_factory=dict)


class ConfigEstadoActualizar(BaseModel):
    """Schema para actualizar configuración de estado"""
    nombre: Optional[str] = None
    color: Optional[str] = None
    posicion_orden: Optional[int] = None
    descripcion: Optional[str] = None
    area: Optional[str] = None
    permisos: Optional[dict] = None


class SubEstadoCrear(BaseModel):
    """Schema para crear sub-estado"""
    estado_id: str  # ObjectId como string
    nombre: str
    descripcion: Optional[str] = None
    posicion_orden: int


class SubEstadoActualizar(BaseModel):
    """Schema para actualizar sub-estado"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    posicion_orden: Optional[int] = None


@router.get("")
async def listar_configuraciones_estado(
    current_user = Depends(get_current_user),
):
    """
    Listar todas las configuraciones de estado ordenadas por posición.
    
    Requiere autenticación.
    """
    try:
        # Obtener todas las configuraciones ordenadas por posicion_orden
        configuraciones = await ConfiguracionEstado.find_all().sort("+posicion_orden").to_list()
        
        # Construir respuesta manualmente para evitar problemas de serialización
        configs_respuesta = []
        
        for config in configuraciones:
            # Convertir ObjectId y datetime a strings
            config_dict = {
                "_id": str(config.id),
                "id": str(config.id),  # Para compatibilidad con frontend
                "nombre": config.nombre,
                "color": config.color,
                "posicion_orden": config.posicion_orden,
                "descripcion": config.descripcion,
                "area": config.area,
                "permisos": config.permisos if isinstance(config.permisos, dict) else {},
                "creado_en": config.creado_en.isoformat() if config.creado_en else None,
                "actualizado_en": config.actualizado_en.isoformat() if config.actualizado_en else None,
            }
            
            # Obtener sub_estados asociados a esta configuración
            sub_estados = await SubEstado.find(
                SubEstado.estado_id == config.id
            ).sort("+posicion_orden").to_list()
            
            config_dict["sub_estados"] = [
                {
                    "_id": str(sub.id),
                    "id": str(sub.id),
                    "estado_id": str(sub.estado_id),
                    "nombre": sub.nombre,
                    "descripcion": sub.descripcion,
                    "posicion_orden": sub.posicion_orden,
                    "creado_en": sub.creado_en.isoformat() if sub.creado_en else None,
                    "actualizado_en": sub.actualizado_en.isoformat() if sub.actualizado_en else None,
                }
                for sub in sub_estados
            ]
            
            configs_respuesta.append(config_dict)
        
        return JSONResponse(content=configs_respuesta)
        
    except Exception as e:
        print(f"❌ Error al listar configuraciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener configuraciones de estado: {str(e)}"
        )


@router.get("/{configuracion_id}")
async def obtener_configuracion_estado(
    configuracion_id: str,
    current_user = Depends(get_current_user),
):
    """
    Obtener detalles de una configuración de estado por ID.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir el ID
        try:
            config_object_id = ObjectId(configuracion_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de configuración inválido"
            )
        
        # Buscar la configuración
        config = await ConfiguracionEstado.get(config_object_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuración de estado con ID {configuracion_id} no encontrada"
            )
        
        # Construir respuesta manualmente
        config_dict = {
            "_id": str(config.id),
            "id": str(config.id),
            "nombre": config.nombre,
            "color": config.color,
            "posicion_orden": config.posicion_orden,
            "descripcion": config.descripcion,
            "area": config.area,
            "permisos": config.permisos if isinstance(config.permisos, dict) else {},
            "creado_en": config.creado_en.isoformat() if config.creado_en else None,
            "actualizado_en": config.actualizado_en.isoformat() if config.actualizado_en else None,
        }
        
        # Obtener sub_estados asociados
        sub_estados = await SubEstado.find(
            SubEstado.estado_id == config.id
        ).sort("+posicion_orden").to_list()
        
        config_dict["sub_estados"] = [
            {
                "_id": str(sub.id),
                "id": str(sub.id),
                "estado_id": str(sub.estado_id),
                "nombre": sub.nombre,
                "descripcion": sub.descripcion,
                "posicion_orden": sub.posicion_orden,
                "creado_en": sub.creado_en.isoformat() if sub.creado_en else None,
                "actualizado_en": sub.actualizado_en.isoformat() if sub.actualizado_en else None,
            }
            for sub in sub_estados
        ]
        
        return JSONResponse(content=config_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al obtener configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener configuración de estado: {str(e)}"
        )


@router.get("/{estado_id}/sub-estados")
async def listar_sub_estados_por_estado(
    estado_id: str,
    current_user = Depends(get_current_user),
):
    """
    Listar sub-estados de un estado específico.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir el ID
        try:
            estado_object_id = ObjectId(estado_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de estado inválido"
            )
        
        # Verificar que el estado exista
        estado = await ConfiguracionEstado.get(estado_object_id)
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {estado_id} no encontrado"
            )
        
        # Obtener sub-estados asociados
        sub_estados = await SubEstado.find(
            SubEstado.estado_id == estado_object_id
        ).sort("+posicion_orden").to_list()
        
        # Construir respuesta
        sub_estados_respuesta = [
            {
                "_id": str(sub.id),
                "id": str(sub.id),
                "estado_id": str(sub.estado_id),
                "nombre": sub.nombre,
                "descripcion": sub.descripcion,
                "posicion_orden": sub.posicion_orden,
                "creado_en": sub.creado_en.isoformat() if sub.creado_en else None,
                "actualizado_en": sub.actualizado_en.isoformat() if sub.actualizado_en else None,
            }
            for sub in sub_estados
        ]
        
        return JSONResponse(content=sub_estados_respuesta)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al listar sub-estados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sub-estados: {str(e)}"
        )


# ============================================
# ENDPOINTS DE CREACIÓN
# ============================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_configuracion_estado(
    datos_configuracion: ConfigEstadoCrear,
    current_user = Depends(get_current_user),
):
    """
    Crear nueva configuración de estado.
    
    Requiere autenticación.
    """
    try:
        # Verificar que no exista un estado con el mismo nombre
        existe = await ConfiguracionEstado.find_one(
            ConfiguracionEstado.nombre == datos_configuracion.nombre
        )
        if existe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un estado con el nombre '{datos_configuracion.nombre}'"
            )
        
        # Crear nuevo estado
        nuevo_estado = ConfiguracionEstado(
            nombre=datos_configuracion.nombre,
            color=datos_configuracion.color,
            posicion_orden=datos_configuracion.posicion_orden,
            descripcion=datos_configuracion.descripcion,
            area=datos_configuracion.area,
            permisos=datos_configuracion.permisos or {},
            creado_en=datetime.utcnow(),
            actualizado_en=datetime.utcnow(),
        )
        
        await nuevo_estado.insert()
        
        # Construir respuesta
        estado_dict = {
            "id": str(nuevo_estado.id),
            "nombre": nuevo_estado.nombre,
            "color": nuevo_estado.color,
            "posicion_orden": nuevo_estado.posicion_orden,
            "descripcion": nuevo_estado.descripcion,
            "area": nuevo_estado.area,
            "permisos": nuevo_estado.permisos,
            "creado_en": nuevo_estado.creado_en.isoformat(),
            "actualizado_en": nuevo_estado.actualizado_en.isoformat(),
            "sub_estados": []
        }
        
        return JSONResponse(content=estado_dict, status_code=status.HTTP_201_CREATED)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al crear estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear estado: {str(e)}"
        )


@router.patch("/{configuracion_id}")
async def actualizar_configuracion_estado(
    configuracion_id: str,
    datos_configuracion: ConfigEstadoActualizar,
    current_user = Depends(get_current_user),
):
    """
    Actualizar configuración de estado.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir el ID
        try:
            config_object_id = ObjectId(configuracion_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de configuración inválido"
            )
        
        # Buscar el estado
        estado = await ConfiguracionEstado.get(config_object_id)
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {configuracion_id} no encontrado"
            )
        
        # Si se cambia el nombre, verificar que no exista otro con ese nombre
        if datos_configuracion.nombre and datos_configuracion.nombre != estado.nombre:
            existe = await ConfiguracionEstado.find_one(
                ConfiguracionEstado.nombre == datos_configuracion.nombre
            )
            if existe:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un estado con el nombre '{datos_configuracion.nombre}'"
                )
        
        # Actualizar campos
        update_data = datos_configuracion.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(estado, field, value)
        
        estado.actualizado_en = datetime.utcnow()
        await estado.save()
        
        # Obtener sub-estados
        sub_estados = await SubEstado.find(
            SubEstado.estado_id == estado.id
        ).sort("+posicion_orden").to_list()
        
        # Construir respuesta
        estado_dict = {
            "id": str(estado.id),
            "nombre": estado.nombre,
            "color": estado.color,
            "posicion_orden": estado.posicion_orden,
            "descripcion": estado.descripcion,
            "area": estado.area,
            "permisos": estado.permisos,
            "creado_en": estado.creado_en.isoformat(),
            "actualizado_en": estado.actualizado_en.isoformat(),
            "sub_estados": [
                {
                    "id": str(sub.id),
                    "estado_id": str(sub.estado_id),
                    "nombre": sub.nombre,
                    "descripcion": sub.descripcion,
                    "posicion_orden": sub.posicion_orden,
                    "creado_en": sub.creado_en.isoformat(),
                    "actualizado_en": sub.actualizado_en.isoformat(),
                }
                for sub in sub_estados
            ]
        }
        
        return JSONResponse(content=estado_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al actualizar estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )


@router.delete("/{configuracion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_configuracion_estado(
    configuracion_id: str,
    current_user = Depends(get_current_user),
):
    """
    Eliminar configuración de estado.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir el ID
        try:
            config_object_id = ObjectId(configuracion_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de configuración inválido"
            )
        
        # Buscar el estado
        estado = await ConfiguracionEstado.get(config_object_id)
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {configuracion_id} no encontrado"
            )
        
        # Verificar si hay reclamos usando este estado
        from app.modules.claims.models_mongodb import Reclamo
        reclamos_con_estado = await Reclamo.find(
            Reclamo.estado_id == config_object_id
        ).count()
        
        if reclamos_con_estado > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede eliminar el estado porque hay {reclamos_con_estado} reclamo(s) usándolo"
            )
        
        # Eliminar sub-estados asociados
        await SubEstado.find(SubEstado.estado_id == config_object_id).delete()
        
        # Eliminar estado
        await estado.delete()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al eliminar estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar estado: {str(e)}"
        )


# ============================================
# ENDPOINTS DE SUB-ESTADOS (CRUD)
# ============================================

@router.post("/{estado_id}/sub-estados", status_code=status.HTTP_201_CREATED)
async def crear_sub_estado(
    estado_id: str,
    datos_sub_estado: SubEstadoCrear,
    current_user = Depends(get_current_user),
):
    """
    Crear nuevo sub-estado para un estado.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir el ID del estado
        try:
            estado_object_id = ObjectId(estado_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de estado inválido"
            )
        
        # Verificar que el estado existe
        estado = await ConfiguracionEstado.get(estado_object_id)
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {estado_id} no encontrado"
            )
        
        # Verificar que no exista un sub-estado con el mismo nombre en este estado
        existe = await SubEstado.find_one(
            SubEstado.estado_id == estado_object_id,
            SubEstado.nombre == datos_sub_estado.nombre
        )
        if existe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un sub-estado con el nombre '{datos_sub_estado.nombre}' en este estado"
            )
        
        # Crear nuevo sub-estado
        nuevo_sub_estado = SubEstado(
            estado_id=estado_object_id,
            nombre=datos_sub_estado.nombre,
            descripcion=datos_sub_estado.descripcion,
            posicion_orden=datos_sub_estado.posicion_orden,
            creado_en=datetime.utcnow(),
            actualizado_en=datetime.utcnow(),
        )
        
        await nuevo_sub_estado.insert()
        
        # Construir respuesta
        sub_estado_dict = {
            "id": str(nuevo_sub_estado.id),
            "estado_id": str(nuevo_sub_estado.estado_id),
            "nombre": nuevo_sub_estado.nombre,
            "descripcion": nuevo_sub_estado.descripcion,
            "posicion_orden": nuevo_sub_estado.posicion_orden,
            "creado_en": nuevo_sub_estado.creado_en.isoformat(),
            "actualizado_en": nuevo_sub_estado.actualizado_en.isoformat(),
        }
        
        return JSONResponse(content=sub_estado_dict, status_code=status.HTTP_201_CREATED)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al crear sub-estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear sub-estado: {str(e)}"
        )


@router.patch("/{estado_id}/sub-estados/{sub_estado_id}")
async def actualizar_sub_estado(
    estado_id: str,
    sub_estado_id: str,
    datos_sub_estado: SubEstadoActualizar,
    current_user = Depends(get_current_user),
):
    """
    Actualizar sub-estado.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir IDs
        try:
            sub_estado_object_id = ObjectId(sub_estado_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de sub-estado inválido"
            )
        
        # Buscar el sub-estado
        sub_estado = await SubEstado.get(sub_estado_object_id)
        if not sub_estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sub-estado con ID {sub_estado_id} no encontrado"
            )
        
        # Si se cambia el nombre, verificar que no exista otro con ese nombre
        if datos_sub_estado.nombre and datos_sub_estado.nombre != sub_estado.nombre:
            existe = await SubEstado.find_one(
                SubEstado.estado_id == sub_estado.estado_id,
                SubEstado.nombre == datos_sub_estado.nombre
            )
            if existe:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un sub-estado con el nombre '{datos_sub_estado.nombre}' en este estado"
                )
        
        # Actualizar campos
        update_data = datos_sub_estado.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sub_estado, field, value)
        
        sub_estado.actualizado_en = datetime.utcnow()
        await sub_estado.save()
        
        # Construir respuesta
        sub_estado_dict = {
            "id": str(sub_estado.id),
            "estado_id": str(sub_estado.estado_id),
            "nombre": sub_estado.nombre,
            "descripcion": sub_estado.descripcion,
            "posicion_orden": sub_estado.posicion_orden,
            "creado_en": sub_estado.creado_en.isoformat(),
            "actualizado_en": sub_estado.actualizado_en.isoformat(),
        }
        
        return JSONResponse(content=sub_estado_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al actualizar sub-estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar sub-estado: {str(e)}"
        )


@router.delete("/{estado_id}/sub-estados/{sub_estado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sub_estado(
    estado_id: str,
    sub_estado_id: str,
    current_user = Depends(get_current_user),
):
    """
    Eliminar sub-estado.
    
    Requiere autenticación.
    """
    try:
        # Validar y convertir ID
        try:
            sub_estado_object_id = ObjectId(sub_estado_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de sub-estado inválido"
            )
        
        # Buscar el sub-estado
        sub_estado = await SubEstado.get(sub_estado_object_id)
        if not sub_estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sub-estado con ID {sub_estado_id} no encontrado"
            )
        
        # Verificar si hay reclamos usando este sub-estado
        from app.modules.claims.models_mongodb import Reclamo
        reclamos_con_sub_estado = await Reclamo.find(
            Reclamo.sub_estado_id == sub_estado_object_id
        ).count()
        
        if reclamos_con_sub_estado > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede eliminar el sub-estado porque hay {reclamos_con_sub_estado} reclamo(s) usándolo"
            )
        
        # Eliminar sub-estado
        await sub_estado.delete()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al eliminar sub-estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar sub-estado: {str(e)}"
        )
