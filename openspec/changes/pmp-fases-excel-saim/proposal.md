## Why

La operación no cuenta con una base única y verificable para medir el cumplimiento del Plan de Mantenimiento Preventivo (PMP), su carga de horas-hombre ni la capacidad requerida por área. Se necesita iniciar con el historial controlado de `JOSE.xlsx`, validarlo contra sus totales y, solo después, mantenerlo actualizado automáticamente desde SAIM sin perder el corte válido ante errores.

## What Changes

- Crear el módulo PMP con órdenes, áreas, personal, programación semanal, historial de cambios y fotografías diarias de cumplimiento.
- Importar exclusivamente `añadidos/JOSE.xlsx` como fuente inicial obligatoria, persistiendo las órdenes válidas y reportando las inconsistentes sin descartar las válidas.
- Usar `Especialidad` como área PMP y `TiempoPlaneado` como el insumo prioritario de horas-hombre en la Fase 1; las fechas planeadas no serán una métrica ni sustituto de fecha de creación.
- Incorporar un tablero PMP con órdenes y horas-hombre totales, finalizadas y pendientes; cumplimiento total y por área; meta estricta superior a 90 %, semáforo, alertas, capacidad, programación semanal y brechas de personal equivalente.
- Retirar de la interfaz y bloquear la creación de reportes manuales de falla, conservando los registros históricos existentes.
- Añadir, después de validar la Fase 1, una integración SAIM protegida por token Bearer cifrado, renovable por administrador y nunca recuperable en pantalla.
- Ejecutar la sincronización SAIM diaria a las 7:00 a. m. de Colombia, con paginación, trazabilidad, fotografías diarias, deduplicación con las órdenes de Excel y protección del último corte válido ante fallos.

## Capabilities

### New Capabilities
- `pmp-management`: Carga inicial, validación, persistencia, análisis de capacidad y visualización del PMP.
- `saim-pmp-synchronization`: Administración segura de credenciales y sincronización incremental de órdenes PMP desde SAIM.

### Modified Capabilities

- Ninguna. No hay especificaciones existentes de comportamiento para el registro manual actual; su retiro se define dentro de `pmp-management`.

## Impact

- Backend FastAPI: nuevas entidades, migraciones, importador de Excel, servicios PMP/SAIM, tareas programadas y endpoints administrativos y de tablero.
- Frontend React: nueva sección PMP, panel de administración de sincronización y eliminación del acceso al formulario de reportes manuales.
- Base de datos PostgreSQL/Supabase: tablas PMP, trazabilidad de carga, token cifrado, ejecución de sincronización y snapshots diarios.
- Insumos de referencia: `añadidos/JOSE.xlsx` y los scripts SAIM, sin incorporar tokens reales al repositorio ni al código.
