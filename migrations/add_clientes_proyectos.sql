"""
Script de migración para agregar tablas de Clientes, Proyectos y TiposProyecto
Ejecutar después de tener el schema actualizado
"""

-- Crear tabla tipos_proyecto
CREATE TABLE IF NOT EXISTS tipos_proyecto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion VARCHAR(200) UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Crear tabla clientes
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(50),
    correo VARCHAR(255) UNIQUE NOT NULL,
    empresa VARCHAR(200),
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índice para búsquedas por correo
CREATE INDEX IF NOT EXISTS idx_clientes_correo ON clientes(correo);

-- Crear tabla proyectos
CREATE TABLE IF NOT EXISTS proyectos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tipo_proyecto_id UUID NOT NULL REFERENCES tipos_proyecto(id) ON DELETE RESTRICT,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_proyectos_cliente ON proyectos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_proyectos_tipo ON proyectos(tipo_proyecto_id);

-- Agregar columna proyecto_id a la tabla reclamos
ALTER TABLE reclamos 
ADD COLUMN IF NOT EXISTS proyecto_id UUID REFERENCES proyectos(id) ON DELETE SET NULL;

-- Índice para búsquedas de reclamos por proyecto
CREATE INDEX IF NOT EXISTS idx_reclamos_proyecto ON reclamos(proyecto_id);

-- Comentarios en las tablas
COMMENT ON TABLE tipos_proyecto IS 'Catálogo de tipos de proyectos de software';
COMMENT ON TABLE clientes IS 'Clientes de la empresa';
COMMENT ON TABLE proyectos IS 'Proyectos asociados a clientes y tipos de proyecto';
COMMENT ON COLUMN reclamos.proyecto_id IS 'Proyecto asociado al reclamo (opcional)';
