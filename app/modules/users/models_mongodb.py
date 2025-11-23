"""
Modelo MongoDB para Usuarios usando Beanie ODM
Reemplazo de app/modules/users/models.py con SQLAlchemy
"""
from beanie import Document, Indexed
from pydantic import EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Literal, Optional, Annotated


class Usuario(Document):
    """
    Modelo de Usuario para MongoDB
    Colección: usuarios
    """
    
    # Campos principales
    email: Annotated[EmailStr, Indexed(unique=True)]  # Índice único automático
    contrasena_hash: str
    nombre: str
    rol: Literal["admin", "manager", "agent", "viewer"]
    
    # Campos opcionales
    telefono: Optional[str] = None
    departamento: Optional[str] = None
    posicion: Optional[str] = None
    area: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Estado
    activo: bool = True
    
    # Timestamps
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "email": "juan.perez@empresa.com",
                "contrasena_hash": "$2b$12$...",
                "nombre": "Juan Pérez",
                "rol": "agent",
                "telefono": "+54911234567",
                "departamento": "Soporte",
                "posicion": "Agente Senior",
                "area": "Técnico",
                "avatar_url": "https://example.com/avatar.jpg",
                "activo": True,
            }
        }
    )
    
    class Settings:
        """Configuración de Beanie"""
        name = "usuarios"  # Nombre de la colección en MongoDB
        
        # Índices adicionales (email ya tiene índice único arriba)
        indexes = [
            "rol",              # Índice simple para filtrar por rol
            "area",             # Índice simple para filtrar por área
            "activo",           # Índice simple para filtrar activos
            [("area", 1), ("rol", 1)],  # Índice compuesto
        ]
    
    # Métodos de utilidad
    def to_dict(self) -> dict:
        """Convierte el documento a diccionario"""
        data = self.dict(by_alias=True)
        data["id"] = str(self.id)
        return data
    
    @classmethod
    async def find_by_email(cls, email: str) -> Optional["Usuario"]:
        """Busca usuario por email"""
        return await cls.find_one(cls.email == email)
    
    @classmethod
    async def find_active_by_area(cls, area: str) -> list["Usuario"]:
        """Encuentra usuarios activos de un área"""
        return await cls.find(
            cls.area == area,
            cls.activo == True
        ).to_list()
    
    @classmethod
    async def count_by_rol(cls, rol: str) -> int:
        """Cuenta usuarios por rol"""
        return await cls.find(cls.rol == rol).count()


# ========================================
# Ejemplo de queries comunes
# ========================================

"""
# 1. Crear usuario
usuario = Usuario(
    email="nuevo@empresa.com",
    contrasena_hash="...",
    nombre="Nuevo Usuario",
    rol="agent"
)
await usuario.insert()

# 2. Buscar por ID
usuario = await Usuario.get("507f1f77bcf86cd799439011")

# 3. Buscar por email
usuario = await Usuario.find_one(Usuario.email == "juan@empresa.com")

# 4. Buscar todos los managers activos
managers = await Usuario.find(
    Usuario.rol == "manager",
    Usuario.activo == True
).to_list()

# 5. Actualizar usuario
usuario = await Usuario.get("507f1f77bcf86cd799439011")
usuario.nombre = "Nuevo Nombre"
usuario.actualizado_en = datetime.utcnow()
await usuario.save()

# 6. Actualizar múltiples documentos
await Usuario.find(Usuario.area == "Ventas").update(
    {"$set": {"departamento": "Comercial"}}
)

# 7. Eliminar usuario (soft delete)
usuario = await Usuario.get("507f1f77bcf86cd799439011")
usuario.activo = False
await usuario.save()

# 8. Eliminar permanentemente
await usuario.delete()

# 9. Contar usuarios por rol
count = await Usuario.find(Usuario.rol == "agent").count()

# 10. Paginación
usuarios = await Usuario.find().skip(20).limit(10).to_list()

# 11. Ordenar
usuarios = await Usuario.find().sort(-Usuario.creado_en).to_list()

# 12. Agregación
pipeline = [
    {"$group": {"_id": "$rol", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
results = await Usuario.aggregate(pipeline).to_list()
"""
