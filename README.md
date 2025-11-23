# Sistema de Gestión de Reclamos - Backend API

API REST desarrollada con FastAPI para gestión de reclamos con autenticación JWT y arquitectura limpia.

## 🚀 Características

- ✅ **FastAPI** con enfoque similar a Django Rest Framework
- ✅ **Programación asíncrona** (async/await) con ASGI
- ✅ **PostgreSQL** con SQLAlchemy async
- ✅ **Autenticación JWT** con roles (admin, agent, customer)
- ✅ **Arquitectura modular** con separación clara de responsabilidades
- ✅ **Paginación** automática en listados
- ✅ **Validación** robusta con Pydantic
- ✅ **Documentación automática** con Swagger/OpenAPI

## 📁 Estructura del Proyecto

```
gr_fastapi_back_app/
├── app/
│   ├── core/                   # Configuración y utilidades centrales
│   │   ├── config.py          # Settings centralizados (similar a Django)
│   │   ├── database.py        # Configuración de SQLAlchemy async
│   │   ├── models.py          # Modelos base y mixins
│   │   ├── security.py        # JWT y hashing de passwords
│   │   └── schemas.py         # Schemas reutilizables (paginación)
│   │
│   └── modules/               # Módulos de la aplicación
│       ├── auth/              # Autenticación y autorización
│       │   ├── dependencies.py    # Dependencies de autenticación
│       │   ├── routers.py        # Endpoints de auth
│       │   ├── schemas.py        # Schemas de auth
│       │   └── services.py       # Lógica de negocio
│       │
│       ├── users/             # Gestión de usuarios/agentes
│       │   ├── models.py         # Modelo User
│       │   ├── routers.py        # Endpoints CRUD
│       │   ├── schemas.py        # Schemas de validación
│       │   └── services.py       # Lógica de negocio
│       │
│       ├── claims/            # Gestión de reclamos
│       │   ├── models.py         # Modelo Claim
│       │   ├── routers.py        # Endpoints CRUD
│       │   ├── schemas.py        # Schemas de validación
│       │   └── services.py       # Lógica de negocio
│       │
│       ├── notes/             # Notas/comentarios
│       │   ├── models.py         # Modelo ClaimNote
│       │   ├── routers.py        # Endpoints CRUD
│       │   ├── schemas.py        # Schemas de validación
│       │   └── services.py       # Lógica de negocio
│       │
│       └── status/            # Configuración de estados
│           ├── models.py         # Modelo StatusConfig
│           ├── routers.py        # Endpoints CRUD
│           ├── schemas.py        # Schemas de validación
│           └── services.py       # Lógica de negocio
│
├── main.py                    # Punto de entrada de la aplicación
├── pyproject.toml            # Dependencias y configuración
├── .env.example              # Ejemplo de variables de entorno
├── .gitignore               # Archivos ignorados por git
└── README.md                # Este archivo

```

## 🛠️ Tecnologías

- **Python 3.11+**
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy 2.0** - ORM con soporte async
- **Pydantic v2** - Validación de datos
- **PostgreSQL** - Base de datos
- **JWT** - Autenticación basada en tokens
- **Uvicorn** - Servidor ASGI

## 📋 Prerrequisitos

- Python 3.11 o superior
- PostgreSQL 15 o superior
- pip o uv

## ⚙️ Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd gr_fastapi_back_app
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -e .
```

4. **Configurar variables de entorno**
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

5. **Crear base de datos**
```sql
-- En PostgreSQL
CREATE DATABASE sistema_reclamos;
```

6. **Ejecutar la aplicación**
```bash
uvicorn main:app --reload
```

La aplicación estará disponible en: http://localhost:8000

## 📚 Documentación API

Una vez iniciada la aplicación, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 Autenticación

La API usa JWT Bearer tokens. Para autenticarte:

1. **Login**: `POST /api/v1/auth/login`
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

2. **Respuesta**:
```json
{
  "token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": { ... }
}
```

3. **Usar el token**: Agregar header en requests:
```
Authorization: Bearer <token>
```

## 🗃️ Modelos de Datos

### User (usuarios/agentes)
- `id`: UUID
- `email`: String (unique)
- `password_hash`: String
- `name`: String
- `role`: Enum (admin, agent, customer)
- `phone`, `department`, `position`: String
- `created_at`, `updated_at`: DateTime

### Claim (reclamos)
- `id`: UUID
- `subject`: String
- `customer_name`: String
- `contact_info`: String
- `description`: Text
- `status`: String
- `priority`: Enum (low, medium, high, urgent)
- `assigned_to`: UUID (FK a User)
- `created_at`, `updated_at`: DateTime

### ClaimNote (notas)
- `id`: UUID
- `claim_id`: UUID (FK a Claim)
- `content`: Text
- `author`: String
- `created_at`, `updated_at`: DateTime

### StatusConfig (estados)
- `id`: UUID
- `name`: String (unique)
- `color`: String
- `order_position`: Integer
- `created_at`, `updated_at`: DateTime

## 🔌 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/logout` - Cerrar sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `GET /api/v1/auth/me` - Usuario actual

### Usuarios
- `GET /api/v1/users` - Listar usuarios
- `GET /api/v1/users/{id}` - Obtener usuario
- `POST /api/v1/users` - Crear usuario (admin)
- `PATCH /api/v1/users/{id}` - Actualizar usuario
- `DELETE /api/v1/users/{id}` - Eliminar usuario (admin)

### Reclamos
- `GET /api/v1/claims` - Listar reclamos (con filtros)
- `GET /api/v1/claims/{id}` - Obtener reclamo
- `POST /api/v1/claims` - Crear reclamo
- `PATCH /api/v1/claims/{id}` - Actualizar reclamo
- `PATCH /api/v1/claims/{id}/assign` - Asignar agente
- `DELETE /api/v1/claims/{id}` - Eliminar reclamo

### Notas
- `GET /api/v1/claims/{claim_id}/notes` - Listar notas
- `POST /api/v1/claims/{claim_id}/notes` - Crear nota
- `PATCH /api/v1/claims/{claim_id}/notes/{id}` - Actualizar nota
- `DELETE /api/v1/claims/{claim_id}/notes/{id}` - Eliminar nota

### Estados
- `GET /api/v1/status-configs` - Listar configuraciones
- `POST /api/v1/status-configs` - Crear configuración (admin)
- `PATCH /api/v1/status-configs/{id}` - Actualizar (admin)
- `DELETE /api/v1/status-configs/{id}` - Eliminar (admin)

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest
```

## 🏗️ Arquitectura

El proyecto sigue los principios de **Clean Architecture** y **Domain-Driven Design**:

1. **Models** (app/modules/*/models.py): Definición de tablas SQLAlchemy
2. **Schemas** (app/modules/*/schemas.py): Validación con Pydantic
3. **Services** (app/modules/*/services.py): Lógica de negocio
4. **Routers** (app/modules/*/routers.py): Endpoints y controladores

### Flujo de una Request

```
Cliente → Router → Dependencies → Service → Database
         ↓
      Schemas (validación)
```

## 🌍 Variables de Entorno

Ver `.env.example` para todas las variables disponibles.

Principales:
- `DATABASE_URL`: Conexión a PostgreSQL
- `SECRET_KEY`: Clave para JWT (cambiar en producción)
- `BACKEND_CORS_ORIGINS`: Orígenes permitidos para CORS

## 📝 Próximas Mejoras

- [ ] Sistema de migrations con Alembic
- [ ] Sistema de permisos granular
- [ ] Recuperación de contraseña por email
- [ ] Upload de archivos adjuntos
- [ ] Dashboard con métricas y KPIs
- [ ] Tests automatizados completos
- [ ] Docker y Docker Compose
- [ ] CI/CD con GitHub Actions

## 👥 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Desarrollado con ❤️ usando FastAPI**
