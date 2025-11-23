# Migración: Clientes y Proyectos

## Descripción
Esta migración agrega las tablas necesarias para gestionar clientes y proyectos en el sistema de reclamos.

## Nuevas Tablas

### 1. `tipos_proyecto`
Catálogo de tipos de proyectos de software:
- Desarrollo Web
- Aplicación Móvil
- Sistema de Gestión
- E-commerce
- API / Microservicios
- Integración de Sistemas
- Migración de Datos
- Soporte y Mantenimiento

### 2. `clientes`
Información de los clientes:
- nombre, apellido
- correo (único)
- teléfono
- empresa
- activo (flag de estado)

### 3. `proyectos`
Proyectos que relacionan clientes con tipos de proyecto:
- nombre del proyecto
- descripción
- cliente_id (FK a clientes)
- tipo_proyecto_id (FK a tipos_proyecto)
- activo (flag de estado)

### 4. Modificación en `reclamos`
Se agrega el campo:
- `proyecto_id` (UUID, FK a proyectos, nullable)

## Cómo aplicar la migración

### Opción 1: Usando psql (Supabase SQL Editor)
1. Ve a tu proyecto en Supabase
2. Abre el SQL Editor
3. Copia y pega el contenido de `add_clientes_proyectos.sql`
4. Ejecuta el script

### Opción 2: Recrear la base de datos con seed completo
```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar seed (incluye la creación de tablas y datos)
python seed_data.py
```

## Verificación
Después de aplicar la migración, verifica que las tablas existan:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tipos_proyecto', 'clientes', 'proyectos');
```

## Endpoints disponibles

### Clientes
- `GET /api/v1/clientes` - Listar clientes
- `GET /api/v1/clientes/{id}` - Obtener cliente por ID
- `POST /api/v1/clientes` - Crear cliente
- `PUT /api/v1/clientes/{id}` - Actualizar cliente
- `DELETE /api/v1/clientes/{id}` - Desactivar cliente

### Tipos de Proyecto
- `GET /api/v1/tipos-proyecto` - Listar tipos de proyecto
- `GET /api/v1/tipos-proyecto/{id}` - Obtener tipo por ID
- `POST /api/v1/tipos-proyecto` - Crear tipo
- `PUT /api/v1/tipos-proyecto/{id}` - Actualizar tipo

### Proyectos
- `GET /api/v1/proyectos` - Listar proyectos
- `GET /api/v1/proyectos/{id}` - Obtener proyecto por ID
- `GET /api/v1/proyectos/cliente/{cliente_id}` - Proyectos de un cliente
- `POST /api/v1/proyectos` - Crear proyecto
- `PUT /api/v1/proyectos/{id}` - Actualizar proyecto
- `DELETE /api/v1/proyectos/{id}` - Desactivar proyecto

## Flujo de uso en el frontend

1. **Seleccionar Tipo de Proyecto**: Usuario selecciona de un dropdown (ej: "Aplicación Móvil")
2. **Filtrar Proyectos**: Se muestran solo proyectos de ese tipo
3. **Seleccionar Proyecto**: Usuario selecciona un proyecto específico (ej: "App Móvil de Gestión")
4. **Auto-completar Cliente**: Los datos del cliente se cargan automáticamente desde el proyecto seleccionado
5. **Crear Reclamo**: El reclamo se crea con `proyecto_id` asociado

## Datos de prueba
El seed incluye:
- 8 tipos de proyecto
- 8 clientes de empresas de software
- 10 proyectos variados
- 3 reclamos ya asociados a proyectos (los primeros 3)
