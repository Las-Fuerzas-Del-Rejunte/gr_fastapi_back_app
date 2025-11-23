-- Migración: Asegurar que la columna se llame sub_estado_id
-- Fecha: 2025-11-06
-- Descripción: Renombrar la columna si existe como 'sub_estado', o verificar que ya existe como 'sub_estado_id'

-- Intentar renombrar solo si la columna 'sub_estado' existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'reclamos' 
          AND column_name = 'sub_estado'
    ) THEN
        ALTER TABLE reclamos RENAME COLUMN sub_estado TO sub_estado_id;
        RAISE NOTICE 'Columna renombrada: sub_estado → sub_estado_id';
    ELSE
        RAISE NOTICE 'La columna sub_estado no existe, probablemente ya se llama sub_estado_id';
    END IF;
END $$;

-- Verificar el resultado final
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'reclamos'
  AND column_name = 'sub_estado_id';
