-- Script de verificación: ¿Qué columnas tiene la tabla reclamos?
-- Fecha: 2025-11-06

-- Ver todas las columnas de la tabla reclamos
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'reclamos'
ORDER BY ordinal_position;

-- Buscar específicamente columnas relacionadas con sub-estado
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'reclamos'
  AND column_name LIKE '%sub%estado%';
