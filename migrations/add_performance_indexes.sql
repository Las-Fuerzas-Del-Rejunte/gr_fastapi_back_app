-- Migración: Agregar índices para mejorar rendimiento
-- Fecha: 2025-11-05
-- Descripción: Índices en columnas frecuentemente consultadas

-- Índice en estado_id de reclamos (para filtrar por estado)
CREATE INDEX IF NOT EXISTS idx_reclamos_estado_id ON reclamos(estado_id);

-- Índice en asignado_a (para filtrar reclamos por agente)
CREATE INDEX IF NOT EXISTS idx_reclamos_asignado_a ON reclamos(asignado_a);

-- Índice en proyecto_id (para consultas de reclamos por proyecto)
CREATE INDEX IF NOT EXISTS idx_reclamos_proyecto_id ON reclamos(proyecto_id);

-- Índice en creado_en (para ordenamiento por fecha)
CREATE INDEX IF NOT EXISTS idx_reclamos_creado_en ON reclamos(creado_en DESC);

-- Índice compuesto para la consulta más común: estado + fecha
CREATE INDEX IF NOT EXISTS idx_reclamos_estado_fecha ON reclamos(estado_id, creado_en DESC);

-- Índice en prioridad (para filtros)
CREATE INDEX IF NOT EXISTS idx_reclamos_prioridad ON reclamos(prioridad);

-- Índice en cliente_id de proyectos (para buscar proyectos por cliente)
CREATE INDEX IF NOT EXISTS idx_proyectos_cliente_id ON proyectos(cliente_id);

-- Índice en tipo_proyecto_id
CREATE INDEX IF NOT EXISTS idx_proyectos_tipo_proyecto_id ON proyectos(tipo_proyecto_id);

-- Índice en reclamo_id de comentarios (para cargar comentarios de un reclamo)
CREATE INDEX IF NOT EXISTS idx_comentarios_reclamo_id ON comentarios_reclamo(reclamo_id);

-- Índice en reclamo_id de adjuntos
CREATE INDEX IF NOT EXISTS idx_adjuntos_reclamo_id ON adjuntos_reclamo(reclamo_id);

-- Índice en reclamo_id de eventos de auditoría
CREATE INDEX IF NOT EXISTS idx_eventos_auditoria_reclamo_id ON eventos_auditoria(reclamo_id);

-- Índice en tipo_evento para filtrar eventos por tipo
CREATE INDEX IF NOT EXISTS idx_eventos_auditoria_tipo_evento ON eventos_auditoria(tipo_evento);

-- Índice en sub_estado_id de reclamos
CREATE INDEX IF NOT EXISTS idx_reclamos_sub_estado_id ON reclamos(sub_estado_id);

-- Verificar índices creados
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('reclamos', 'proyectos', 'comentarios_reclamo', 'adjuntos_reclamo', 'eventos_auditoria')
ORDER BY tablename, indexname;
