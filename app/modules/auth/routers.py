"""
Router de Autenticación - Endpoints de la API - Adaptado para MongoDB/Beanie
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import InvalidCredentialsException, UserNotFoundException
from app.modules.auth.schemas import (
    SolicitudLogin,
    RespuestaToken,
    SolicitudRefreshToken,
    SolicitudOlvideContrasena,
    SolicitudRestablecerContrasena,
    RespuestaMensaje,
)
from app.modules.auth.services import AuthService
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models_mongodb import Usuario

router = APIRouter(prefix="/autenticacion", tags=["autenticacion"])


@router.post("/login", response_model=RespuestaToken)
async def login(
    credenciales: SolicitudLogin,
):
    """
    Iniciar sesión en el sistema.
    
    Retorna tokens JWT de acceso y refresh junto con los datos del usuario.
    """
    try:
        # Autenticar y generar tokens
        tokens = await AuthService.login(
            credenciales.email,
            credenciales.contrasena
        )
        
        # Obtener datos del usuario
        usuario = await Usuario.find_one(Usuario.email == credenciales.email)
        
        # Convertir usuario de Beanie a dict para la respuesta
        usuario_dict = usuario.model_dump(by_alias=True)
        
        return RespuestaToken(
            token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            usuario=usuario_dict,
        )
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", response_model=RespuestaMensaje)
async def logout(
    usuario_actual = Depends(get_current_user),
):
    """
    Cerrar sesión (invalidar token).
    
    En una implementación real, se debería agregar el token a una blacklist.
    Por ahora, solo retorna un mensaje de éxito.
    """
    # TODO: Implementar blacklist de tokens
    return RespuestaMensaje(mensaje="Sesión cerrada exitosamente")


@router.post("/refresh", response_model=RespuestaToken)
async def refrescar_token(
    datos_refresh: SolicitudRefreshToken,
):
    """
    Renovar token de acceso usando refresh token.
    """
    try:
        # Renovar access token
        tokens = await AuthService.refresh_access_token(datos_refresh.refresh_token)
        
        # Obtener usuario para incluir en respuesta
        usuario = await AuthService.verify_refresh_token(datos_refresh.refresh_token)
        
        if not usuario:
            raise InvalidCredentialsException("Usuario no encontrado")
        
        # Convertir usuario a dict
        usuario_dict = usuario.model_dump(by_alias=True)
        
        return RespuestaToken(
            token=tokens["access_token"],
            refresh_token=datos_refresh.refresh_token,  # Mantener el mismo refresh token
            usuario=usuario_dict,
        )
    except (InvalidCredentialsException, UserNotFoundException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/olvide-contrasena", response_model=RespuestaMensaje)
async def olvide_contrasena(
    solicitud: SolicitudOlvideContrasena,
):
    """
    Solicitar recuperación de contraseña.
    
    Envía un email con un token de recuperación.
    TODO: Implementar envío de email
    """
    usuario = await Usuario.find_one(Usuario.email == solicitud.email)
    
    # Por seguridad, siempre retornar el mismo mensaje
    # aunque el usuario no exista
    if usuario:
        # TODO: Generar token de recuperación
        # TODO: Enviar email
        pass
    
    return RespuestaMensaje(mensaje="Email de recuperación enviado")


@router.post("/restablecer-contrasena", response_model=RespuestaMensaje)
async def restablecer_contrasena(
    solicitud: SolicitudRestablecerContrasena,
):
    """
    Restablecer contraseña con token de recuperación.
    
    TODO: Implementar sistema de tokens de recuperación
    """
    # TODO: Verificar token de recuperación
    # TODO: Actualizar contraseña del usuario
    
    return RespuestaMensaje(mensaje="Contraseña restablecida exitosamente")


@router.get("/yo", response_model=RespuestaToken)
async def obtener_usuario_actual(
    usuario_actual = Depends(get_current_user),
):
    """
    Obtener información del usuario actual autenticado.
    """
    # Generar nuevos tokens (opcional)
    tokens = AuthService.generate_tokens(str(usuario_actual.id))
    
    # Convertir usuario a dict
    usuario_dict = usuario_actual.model_dump(by_alias=True)
    
    return RespuestaToken(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        usuario=usuario_dict,
    )
