"""
Ejemplo de servicio actualizado para usar Beanie ODM en lugar de SQLAlchemy
Este archivo muestra cómo adaptar los servicios existentes a MongoDB
"""
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Modelos MongoDB
from app.modules.users.models_mongodb import Usuario

# Schemas Pydantic (se mantienen iguales)
from app.modules.users.schemas import UserCreate, UserUpdate, UserResponse

# Excepciones
from fastapi import HTTPException, status


class UserServiceMongoDB:
    """
    Servicio de usuarios usando MongoDB con Beanie
    Reemplaza la versión con SQLAlchemy
    """
    
    # ========================================
    # CREATE - Crear usuario
    # ========================================
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> Usuario:
        """
        Crea un nuevo usuario en MongoDB
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el email ya existe
        """
        # Verificar si el email ya existe
        existing_user = await Usuario.find_one(Usuario.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Crear usuario
        usuario = Usuario(
            email=user_data.email,
            contrasena_hash=user_data.contrasena_hash,  # Ya debe venir hasheada
            nombre=user_data.nombre,
            rol=user_data.rol,
            telefono=user_data.telefono,
            departamento=user_data.departamento,
            posicion=user_data.posicion,
            area=user_data.area,
            avatar_url=user_data.avatar_url,
            activo=True,
        )
        
        # Insertar en MongoDB
        await usuario.insert()
        
        return usuario
    
    # ========================================
    # READ - Leer usuarios
    # ========================================
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Usuario:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario (ObjectId o string)
            
        Returns:
            Usuario encontrado
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        try:
            # Convertir string a ObjectId si es necesario
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            usuario = await Usuario.get(user_id)
            
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
            
            return usuario
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID inválido: {str(e)}"
            )
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Usuario]:
        """
        Busca un usuario por email
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        return await Usuario.find_one(Usuario.email == email)
    
    @staticmethod
    async def get_all_users(
        skip: int = 0,
        limit: int = 100,
        rol: Optional[str] = None,
        area: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> List[Usuario]:
        """
        Obtiene lista de usuarios con filtros y paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            rol: Filtrar por rol (opcional)
            area: Filtrar por área (opcional)
            activo: Filtrar por estado activo (opcional)
            
        Returns:
            Lista de usuarios
        """
        # Construir query dinámicamente
        query = Usuario.find()
        
        # Aplicar filtros si existen
        if rol:
            query = query.find(Usuario.rol == rol)
        
        if area:
            query = query.find(Usuario.area == area)
        
        if activo is not None:
            query = query.find(Usuario.activo == activo)
        
        # Aplicar paginación y ordenar
        usuarios = await query.sort(-Usuario.creado_en).skip(skip).limit(limit).to_list()
        
        return usuarios
    
    @staticmethod
    async def search_users(search_term: str) -> List[Usuario]:
        """
        Busca usuarios por nombre o email
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de usuarios que coinciden
        """
        # Búsqueda con regex (case-insensitive)
        usuarios = await Usuario.find(
            {
                "$or": [
                    {"nombre": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}},
                ]
            }
        ).to_list()
        
        return usuarios
    
    # ========================================
    # UPDATE - Actualizar usuario
    # ========================================
    
    @staticmethod
    async def update_user(user_id: str, user_update: UserUpdate) -> Usuario:
        """
        Actualiza un usuario existente
        
        Args:
            user_id: ID del usuario
            user_update: Datos a actualizar
            
        Returns:
            Usuario actualizado
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        # Obtener usuario
        usuario = await UserServiceMongoDB.get_user_by_id(user_id)
        
        # Actualizar solo los campos proporcionados
        update_data = user_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(usuario, field, value)
        
        # Actualizar timestamp
        usuario.actualizado_en = datetime.utcnow()
        
        # Guardar cambios
        await usuario.save()
        
        return usuario
    
    @staticmethod
    async def deactivate_user(user_id: str) -> Usuario:
        """
        Desactiva un usuario (soft delete)
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario desactivado
        """
        usuario = await UserServiceMongoDB.get_user_by_id(user_id)
        usuario.activo = False
        usuario.actualizado_en = datetime.utcnow()
        await usuario.save()
        return usuario
    
    # ========================================
    # DELETE - Eliminar usuario
    # ========================================
    
    @staticmethod
    async def delete_user(user_id: str) -> dict:
        """
        Elimina permanentemente un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Confirmación de eliminación
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        usuario = await UserServiceMongoDB.get_user_by_id(user_id)
        await usuario.delete()
        
        return {"message": "Usuario eliminado exitosamente", "id": str(usuario.id)}
    
    # ========================================
    # ESTADÍSTICAS Y AGREGACIONES
    # ========================================
    
    @staticmethod
    async def count_users_by_rol() -> dict:
        """
        Cuenta usuarios agrupados por rol
        
        Returns:
            Diccionario con conteo por rol
        """
        pipeline = [
            {"$group": {"_id": "$rol", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await Usuario.aggregate(pipeline).to_list()
        
        # Formatear resultados
        return {item["_id"]: item["count"] for item in results}
    
    @staticmethod
    async def get_users_by_area(area: str) -> List[Usuario]:
        """
        Obtiene todos los usuarios activos de un área específica
        
        Args:
            area: Nombre del área
            
        Returns:
            Lista de usuarios del área
        """
        return await Usuario.find(
            Usuario.area == area,
            Usuario.activo == True
        ).to_list()


# ========================================
# Ejemplo de uso en routers
# ========================================

"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar permisos (solo admin puede crear usuarios)
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Crear usuario usando servicio MongoDB
    usuario = await UserServiceMongoDB.create_user(user_data)
    
    return usuario


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    rol: Optional[str] = None,
    area: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user)
):
    usuarios = await UserServiceMongoDB.get_all_users(
        skip=skip,
        limit=limit,
        rol=rol,
        area=area
    )
    return usuarios


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    usuario = await UserServiceMongoDB.get_user_by_id(user_id)
    return usuario


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar permisos
    if current_user.rol not in ["admin", "manager"] and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    usuario = await UserServiceMongoDB.update_user(user_id, user_update)
    return usuario


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    # Solo admin puede eliminar
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    result = await UserServiceMongoDB.delete_user(user_id)
    return result
"""
