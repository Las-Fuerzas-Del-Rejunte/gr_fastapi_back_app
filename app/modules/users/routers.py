"""
Router de Usuarios - Endpoints de la API - Adaptado para MongoDB
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.schemas import PaginatedResponse, PaginationMeta
from app.modules.users.schemas_mongodb import (
    UsuarioCrear,
    UsuarioRespuesta,
    UsuarioActualizar,
    UsuarioCambiarContrasena,
)
from app.modules.users.services import UserService
from app.modules.auth.dependencies import get_current_user, require_role
from app.core.exceptions import UserNotFoundException, DuplicateException

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=PaginatedResponse[UsuarioRespuesta])
async def listar_usuarios(
    rol: Optional[Literal["admin", "manager", "agent", "viewer"]] = Query(None, description="Filtrar por rol"),
    area: Optional[str] = Query(None, description="Filtrar por área"),
    activo: Optional[bool] = Query(None, description="Filtrar por activos/inactivos"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    limite: int = Query(20, ge=1, le=100, description="Items por página"),
    usuario_actual = Depends(get_current_user),
):
    """
    Listar usuarios/agentes del sistema.
    
    Requiere autenticación.
    """
    saltar = (pagina - 1) * limite
    usuarios, total = await UserService.get_all(
        role=rol,
        area=area,
        activo=activo,
        skip=saltar,
        limit=limite
    )
    
    # Convertir usuarios a dict
    usuarios_dict = [u.model_dump(by_alias=True) for u in usuarios]
    
    total_paginas = (total + limite - 1) // limite
    
    return {
        "datos": usuarios_dict,
        "paginacion": PaginationMeta(
            pagina=pagina,
            limite=limite,
            total=total,
            total_paginas=total_paginas
        )
    }


@router.get("/{usuario_id}", response_model=UsuarioRespuesta)
async def obtener_usuario(
    usuario_id: str,
    usuario_actual = Depends(get_current_user),
):
    """
    Obtener detalles de un usuario específico.
    
    Requiere autenticación.
    """
    try:
        usuario = await UserService.get_by_id(usuario_id)
        
        if not usuario:
            raise UserNotFoundException(f"Usuario {usuario_id} no encontrado")
        
        return usuario.model_dump(by_alias=True)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    datos_usuario: UsuarioCrear,
    usuario_actual = Depends(require_role("admin")),
):
    """
    Crear nuevo usuario.
    
    Requiere rol de administrador.
    """
    try:
        usuario = await UserService.create_user(datos_usuario)
        return usuario.model_dump(by_alias=True)
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/crearUsuarioRol", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_usuario_con_rol(
    datos_usuario: UsuarioCrear,
    usuario_actual = Depends(require_role("admin")),
):
    """
    Crear nuevo usuario con rol específico.
    
    Endpoint alternativo para compatibilidad con frontend.
    Requiere rol de administrador.
    """
    try:
        usuario = await UserService.create_user(datos_usuario)
        return usuario.model_dump(by_alias=True)
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/{usuario_id}", response_model=UsuarioRespuesta)
async def actualizar_usuario(
    usuario_id: str,
    datos_usuario: UsuarioActualizar,
    usuario_actual = Depends(get_current_user),
):
    """
    Actualizar usuario.
    
    Los usuarios pueden actualizar su propio perfil.
    Los administradores pueden actualizar cualquier usuario.
    """
    # Verificar permisos
    if str(usuario_actual.id) != usuario_id and usuario_actual.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )
    
    try:
        usuario_actualizado = await UserService.update_user(usuario_id, datos_usuario)
        return usuario_actualizado.model_dump(by_alias=True)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    usuario_id: str,
    usuario_actual = Depends(require_role("admin")),
):
    """
    Eliminar usuario (soft delete).
    
    Requiere rol de administrador.
    """
    try:
        await UserService.delete_user(usuario_id)
        return None
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{usuario_id}/cambiar-contrasena", status_code=status.HTTP_200_OK)
async def cambiar_contrasena(
    usuario_id: str,
    datos_contrasena: UsuarioCambiarContrasena,
    usuario_actual = Depends(get_current_user),
):
    """
    Cambiar contraseña de usuario.
    
    Los usuarios solo pueden cambiar su propia contraseña.
    """
    if str(usuario_actual.id) != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes cambiar la contraseña de otro usuario"
        )
    
    from app.core.security import verify_password
    
    # Verificar contraseña actual
    if not verify_password(datos_contrasena.contrasena_actual, usuario_actual.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    try:
        await UserService.change_password(usuario_id, datos_contrasena.contrasena_nueva)
        return {"mensaje": "Contraseña actualizada exitosamente"}
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
