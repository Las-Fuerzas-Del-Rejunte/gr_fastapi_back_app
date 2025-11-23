"""
Servicios de Usuario - Adaptado para MongoDB/Beanie
"""
from typing import List, Optional, Literal
from bson import ObjectId

from app.modules.users.models_mongodb import Usuario
from app.modules.users.schemas_mongodb import UsuarioCrear, UsuarioActualizar
from app.core.security import get_password_hash
from app.core.exceptions import UserNotFoundException, DuplicateException


class UserService:
    """Servicio para operaciones de usuarios con MongoDB"""
    
    @staticmethod
    async def get_by_id(user_id: str | ObjectId) -> Optional[Usuario]:
        """Obtener usuario por ID"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            return await Usuario.get(user_id)
        except Exception:
            return None
    
    @staticmethod
    async def get_by_email(email: str) -> Optional[Usuario]:
        """Obtener usuario por email"""
        return await Usuario.find_one(Usuario.email == email)
    
    @staticmethod
    async def get_all(
        role: Optional[Literal["admin", "manager", "agent", "viewer"]] = None,
        area: Optional[str] = None,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Usuario], int]:
        """
        Obtener lista de usuarios con paginación
        
        Returns:
            Tupla de (lista de usuarios, total count)
        """
        # Construir filtros
        filters = []
        
        if role:
            filters.append(Usuario.rol == role)
        
        if area:
            filters.append(Usuario.area == area)
            
        if activo is not None:
            filters.append(Usuario.activo == activo)
        
        # Obtener usuarios con paginación
        if filters:
            usuarios = await Usuario.find(*filters).sort("-creado_en").skip(skip).limit(limit).to_list()
            total = await Usuario.find(*filters).count()
        else:
            usuarios = await Usuario.find_all().sort("-creado_en").skip(skip).limit(limit).to_list()
            total = await Usuario.find_all().count()
        
        return usuarios, total
    
    @staticmethod
    async def create_user(user_data: UsuarioCrear) -> Usuario:
        """
        Crear nuevo usuario
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            Usuario creado
            
        Raises:
            DuplicateException: Si el email ya existe
        """
        # Verificar que el email no exista
        existing_user = await UserService.get_by_email(user_data.email)
        if existing_user:
            raise DuplicateException(f"El email {user_data.email} ya está registrado")
        
        # Hash de la contraseña
        hashed_password = get_password_hash(user_data.contrasena)
        
        # Crear usuario
        db_user = Usuario(
            email=user_data.email,
            nombre=user_data.nombre,
            rol=user_data.rol,
            contrasena_hash=hashed_password,
            telefono=user_data.telefono,
            departamento=user_data.departamento,
            posicion=user_data.posicion,
            area=user_data.area,
            avatar_url=user_data.avatar_url,
            activo=user_data.activo,
        )
        
        await db_user.insert()
        return db_user
    
    @staticmethod
    async def update_user(user_id: str | ObjectId, user_data: UsuarioActualizar) -> Usuario:
        """
        Actualizar usuario
        
        Args:
            user_id: ID del usuario
            user_data: Datos a actualizar
            
        Returns:
            Usuario actualizado
            
        Raises:
            UserNotFoundException: Si el usuario no existe
        """
        usuario = await UserService.get_by_id(user_id)
        
        if not usuario:
            raise UserNotFoundException("Usuario no encontrado")
        
        # Actualizar campos que no son None
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(usuario, field, value)
        
        await usuario.save()
        return usuario
    
    @staticmethod
    async def delete_user(user_id: str | ObjectId) -> bool:
        """
        Eliminar usuario (soft delete - marcar como inactivo)
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se eliminó exitosamente
            
        Raises:
            UserNotFoundException: Si el usuario no existe
        """
        usuario = await UserService.get_by_id(user_id)
        
        if not usuario:
            raise UserNotFoundException("Usuario no encontrado")
        
        usuario.activo = False
        await usuario.save()
        return True
    
    @staticmethod
    async def change_password(user_id: str | ObjectId, new_password: str) -> Usuario:
        """
        Cambiar contraseña de usuario
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña en texto plano
            
        Returns:
            Usuario actualizado
            
        Raises:
            UserNotFoundException: Si el usuario no existe
        """
        usuario = await UserService.get_by_id(user_id)
        
        if not usuario:
            raise UserNotFoundException("Usuario no encontrado")
        
        usuario.contrasena_hash = get_password_hash(new_password)
        await usuario.save()
        return usuario
