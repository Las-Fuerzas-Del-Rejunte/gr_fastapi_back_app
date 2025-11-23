# 🔄 ACTUALIZACIÓN DE AUDITORÍA - 23 Noviembre 2025

## 📌 Resumen del Cambio

Se ha mejorado el sistema de auditoría para incluir **nombres legibles** además de los ObjectIds, facilitando la visualización de cambios en el frontend sin consultas adicionales a la base de datos.

---

## ✨ Nuevo Formato de Eventos de Auditoría

### Estructura del Evento de Auditoría

```typescript
interface EventoAuditoria {
  tipo_evento: string;                    // "creacion" | "actualizacion"
  usuario_id: string;                     // ObjectId del usuario
  nombre_usuario: string;                 // Nombre completo del usuario
  area_usuario: string | null;            // Área del usuario
  cambios: CambioAuditoria;              // Detalles del cambio
  descripcion: string;                    // Descripción del evento
  creado_en: string;                      // ISO timestamp
}

interface CambioAuditoria {
  campo: string;                          // "estado_id" | "sub_estado_id" | "prioridad"
  valor_anterior: string | null;          // ObjectId o valor anterior
  valor_nuevo: string | null;             // ObjectId o valor nuevo
  nombre_anterior?: string | null;        // 🆕 NUEVO: Nombre legible anterior
  nombre_nuevo?: string | null;           // 🆕 NUEVO: Nombre legible nuevo
}
```

---

## 📊 Ejemplos por Tipo de Campo

### 1️⃣ Cambio de Estado (`estado_id`)

```json
{
  "tipo_evento": "actualizacion",
  "usuario_id": "69126244b51ea6bf614aac42",
  "nombre_usuario": "Carlos Administrador",
  "area_usuario": "Administración",
  "cambios": {
    "campo": "estado_id",
    "valor_anterior": "69126246b51ea6bf614aac5f",
    "nombre_anterior": "Nuevo",
    "valor_nuevo": "69126246b51ea6bf614aac60",
    "nombre_nuevo": "En Proceso"
  },
  "descripcion": "Campo 'estado_id' actualizado",
  "creado_en": "2025-11-23T10:30:00.000Z"
}
```

**💡 Cómo mostrarlo en el frontend:**
```typescript
const evento = reclamo.eventos_auditoria[0];
const cambio = evento.cambios;

// Opción 1: Usar nombres legibles (RECOMENDADO)
const mensaje = `${evento.nombre_usuario} cambió el estado de "${cambio.nombre_anterior}" a "${cambio.nombre_nuevo}"`;
// Output: "Carlos Administrador cambió el estado de "Nuevo" a "En Proceso"

// Opción 2: Si necesitas los ObjectIds para alguna operación
const estadoAnteriorId = cambio.valor_anterior;
const estadoNuevoId = cambio.valor_nuevo;
```

---

### 2️⃣ Cambio de Sub-Estado (`sub_estado_id`)

```json
{
  "tipo_evento": "actualizacion",
  "usuario_id": "69126244b51ea6bf614aac43",
  "nombre_usuario": "Ana López",
  "area_usuario": "Soporte Técnico",
  "cambios": {
    "campo": "sub_estado_id",
    "valor_anterior": "69126247b51ea6bf614aac63",
    "nombre_anterior": "Solucionado",
    "valor_nuevo": "69126247b51ea6bf614aac64",
    "nombre_nuevo": "Verificado por QA"
  },
  "descripcion": "Campo 'sub_estado_id' actualizado",
  "creado_en": "2025-11-23T11:45:00.000Z"
}
```

**💡 Cómo mostrarlo:**
```typescript
const cambio = evento.cambios;
const mensaje = `${evento.nombre_usuario} actualizó el sub-estado a "${cambio.nombre_nuevo}"`;
// Output: "Ana López actualizó el sub-estado a "Verificado por QA"
```

---

### 3️⃣ Cambio de Prioridad (`prioridad`)

```json
{
  "tipo_evento": "actualizacion",
  "usuario_id": "69126244b51ea6bf614aac42",
  "nombre_usuario": "Carlos Administrador",
  "area_usuario": "Administración",
  "cambios": {
    "campo": "prioridad",
    "valor_anterior": "medium",
    "nombre_anterior": "medium",
    "valor_nuevo": "high",
    "nombre_nuevo": "high"
  },
  "descripcion": "Campo 'prioridad' actualizado",
  "creado_en": "2025-11-23T12:00:00.000Z"
}
```

**💡 Cómo mostrarlo:**
```typescript
// Para prioridad, puedes mapear los valores a español
const prioridadMap = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
  critical: "Crítica"
};

const cambio = evento.cambios;
const mensaje = `${evento.nombre_usuario} cambió la prioridad de ${prioridadMap[cambio.nombre_anterior]} a ${prioridadMap[cambio.nombre_nuevo]}`;
// Output: "Carlos Administrador cambió la prioridad de Media a Alta"
```

---

## 🎨 Componente React Ejemplo

```typescript
interface EventoAuditoriaProps {
  evento: EventoAuditoria;
}

const EventoAuditoriaItem: React.FC<EventoAuditoriaProps> = ({ evento }) => {
  const { cambios, nombre_usuario, creado_en, area_usuario } = evento;
  
  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const obtenerMensajeCambio = () => {
    const { campo, nombre_anterior, nombre_nuevo } = cambios;
    
    switch (campo) {
      case 'estado_id':
        return `cambió el estado de "${nombre_anterior}" a "${nombre_nuevo}"`;
      
      case 'sub_estado_id':
        return `actualizó el sub-estado a "${nombre_nuevo}"`;
      
      case 'prioridad':
        const prioridadMap: Record<string, string> = {
          low: 'Baja',
          medium: 'Media',
          high: 'Alta',
          critical: 'Crítica'
        };
        return `cambió la prioridad de ${prioridadMap[nombre_anterior || '']} a ${prioridadMap[nombre_nuevo || '']}`;
      
      default:
        return `actualizó ${campo}`;
    }
  };
  
  return (
    <div className="auditoria-item">
      <div className="auditoria-header">
        <strong>{nombre_usuario}</strong>
        {area_usuario && <span className="area">({area_usuario})</span>}
      </div>
      <div className="auditoria-mensaje">
        {obtenerMensajeCambio()}
      </div>
      <div className="auditoria-fecha">
        {formatearFecha(creado_en)}
      </div>
    </div>
  );
};
```

---

## 🔄 Migración del Código Existente

### ❌ Código Anterior (Requería consultas adicionales)
```typescript
// Frontend tenía que hacer consultas adicionales para obtener nombres
const estadoId = cambio.valor_nuevo;
const estado = await fetch(`/api/estados/${estadoId}`);
const estadoNombre = estado.nombre;
```

### ✅ Código Nuevo (Todo incluido en el evento)
```typescript
// Ahora todo está incluido en el evento
const estadoNombre = cambio.nombre_nuevo;
// ¡Sin consultas adicionales necesarias!
```

---

## 📋 Checklist de Actualización para el Frontend

- [ ] Actualizar interfaces TypeScript con los nuevos campos `nombre_anterior` y `nombre_nuevo`
- [ ] Modificar componentes de visualización de auditoría para usar `nombre_anterior` y `nombre_nuevo`
- [ ] Eliminar consultas adicionales a endpoints de estados/sub-estados para obtener nombres
- [ ] Probar con diferentes tipos de cambios (estado, sub-estado, prioridad)
- [ ] Verificar que los eventos de auditoría antiguos (sin `nombre_anterior`/`nombre_nuevo`) se manejen correctamente

---

## ⚠️ Compatibilidad con Eventos Antiguos

Los eventos de auditoría creados **antes de esta actualización** NO tendrán los campos `nombre_anterior` y `nombre_nuevo`. Recomendación:

```typescript
const obtenerNombre = (cambio: CambioAuditoria, tipo: 'anterior' | 'nuevo') => {
  // Intentar usar el nombre legible
  const nombreKey = tipo === 'anterior' ? 'nombre_anterior' : 'nombre_nuevo';
  
  if (cambio[nombreKey]) {
    return cambio[nombreKey];
  }
  
  // Fallback: mostrar el ObjectId o hacer consulta si es necesario
  const valorKey = tipo === 'anterior' ? 'valor_anterior' : 'valor_nuevo';
  return cambio[valorKey] || 'N/A';
};
```

---

## ✅ Ventajas de esta Actualización

1. **🚀 Mejor Performance**: No requiere consultas adicionales a la base de datos
2. **🎯 Más Simple**: Frontend no necesita mapear ObjectIds a nombres
3. **📱 Offline-Ready**: Toda la información está en el evento, funciona sin conexión
4. **🐛 Menos Errores**: Elimina casos donde el ObjectId no se encuentra o el estado fue eliminado
5. **👁️ Mejor UX**: Mensajes de auditoría más legibles y rápidos de cargar

---

## 🆘 Soporte

Si tienes dudas o problemas con la integración, contacta al equipo de backend.

**Fecha de implementación**: 23 de Noviembre de 2025
**Versión del backend**: Compatible con todas las versiones que usen MongoDB
