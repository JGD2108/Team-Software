## Context

La aplicación usa FastAPI, SQLAlchemy y PostgreSQL/Supabase en el backend, con una SPA React en el frontend. El esquema actual cubre eventos de mantenimiento, catálogos y reportes manuales, pero no modela órdenes PMP, capacidad, programación ni sincronización externa. Véase `proposal.md` para la motivación y las especificaciones de esta propuesta para el comportamiento observable.

`JOSE.xlsx` es una sola hoja con 1.082 filas y encabezados repetidos para Activo. Su lectura necesita un mapeo posicional estable: Especialidad corresponde al área PMP, TiempoPlaneado a minutos planeados y el identificador de orden es el candidato a identificador externo. El archivo contiene filas inconsistentes y órdenes repetidas, por lo que la fuente debe preservarse y cada resultado debe ser auditable.

## Goals / Non-Goals

**Goals:**

- Separar claramente la carga única de Excel de la sincronización continua SAIM.
- Mantener datos atómicos, trazables y deduplicados para alimentar tablero, capacidad y snapshots.
- Aplicar controles seguros al token y controles transaccionales al corte de sincronización.
- Permitir comprobación automática de las reglas y totales establecidos para la Fase 1.

**Non-Goals:**

- Inferir una fecha de creación desde fechas planeadas del Excel.
- Inventar la clasificación PMP o el nombre de horas-hombre en SAIM antes de observar una respuesta autenticada válida.
- Migrar, transformar o eliminar los eventos manuales históricos.
- Convertir los scripts de Google Apps Script en componentes de producción sin adaptarlos al backend.

## Decisions

### Modelo PMP separado de eventos de falla

Se añadirán entidades para áreas PMP, órdenes, importaciones y errores de importación, personal, turnos/asignaciones semanales, historial de cambios, configuración SAIM, ejecuciones de sincronización y snapshots. Las órdenes conservarán `external_id`, origen (`excel` o `saim`), estado, área, minutos planeados, datos fuente y marca de vigencia. Las restricciones únicas y la actualización por identificador externo evitarán duplicados entre orígenes.

Alternativa considerada: reutilizar `MaintenanceEvent`. Se descarta porque representa fallas puntuales y no contiene planificación, estado de orden ni horas-hombre.

### Importador exclusivo y mapeo explícito de JOSE.xlsx

El importador aceptará el archivo inicial designado y asignará columnas repetidas por su índice, no por nombre ambiguo. Validará identificador, Especialidad, estado permitido y TiempoPlaneado positivo; guardará el resultado de cada fila y calculará la reconciliación usando solamente las válidas. El valor de TiempoPlaneado se normalizará a horas para presentación, conservando el valor original en minutos para exactitud.

Alternativa considerada: inferir campos por texto de encabezado. Se descarta por los cinco encabezados `Activo` repetidos y el riesgo de reasignar columnas silenciosamente.

### Métricas y capacidad con reglas centralizadas

Un servicio de dominio calculará órdenes y horas totales, finalizadas y pendientes, cumplimiento, semáforo, alertas y brechas. El cumplimiento se calculará como órdenes finalizadas válidas sobre órdenes válidas del alcance, y la condición verde será `> 90`, no `>= 90`. La brecha comparará minutos pendientes con minutos de capacidad programada; el FTE requerido utilizará la capacidad semanal configurable de cada área/turno para evitar asumir una jornada universal.

Alternativa considerada: cálculos en el frontend. Se descarta para que los snapshots, API, PDF y tablero usen el mismo resultado verificable.

### Token cifrado y sincronización transaccional

La configuración guardará un cifrado autenticado del token, con la clave fuera de la base de datos y del repositorio. La API administrativa solo indicará si existe una credencial y su fecha de actualización. Cada ejecución SAIM consultará `/ordenes` con Bearer, paginación por `rows` y `page`, y verificará respuesta/total antes de modificar el corte. La aplicación reunirá y validará el conjunto completo antes de aplicar un upsert transaccional y generar su snapshot; un error deja intacto el último corte exitoso.

Alternativa considerada: actualizar por página. Se descarta porque una página fallida dejaría un corte parcial e inconsistente.

### Programación a las 7:00 de Colombia y ejecución recuperable

El trabajo se programará en `America/Bogota` mediante un mecanismo compatible con el despliegue configurado. La operación se expondrá además como ejecución controlada para administradores y pruebas. La tabla de ejecuciones almacenará inicio, final, estado, conteos, error seguro y la referencia al snapshot, permitiendo observar el último resultado sin registrar secretos.

Alternativa considerada: usar horario UTC fijo. Se descarta para preservar el requisito de negocio de 7:00 a. m. Colombia.

### Retiro controlado de reportes manuales

La navegación y componentes de creación manual se eliminarán del frontend y el endpoint de creación será retirado o deshabilitado explícitamente. Las consultas de histórico continuarán operativas para no afectar auditoría ni datos existentes.

Alternativa considerada: ocultar únicamente el botón. Se descarta porque el endpoint seguiría permitiendo nuevas inserciones.

## Risks / Trade-offs

- [El Excel contiene 2 tiempos vacíos, 5 `SIN ASIGNAR` y duplicados] → Validar por fila, guardar los errores y definir reglas explícitas de identificador único; no sumar filas inválidas.
- [La fuente no tiene fecha de creación ni área explícita] → Usar Especialidad como área por decisión de negocio y dejar fecha de creación vacía para Fase 1, sin derivarla de fechas planeadas.
- [El esquema de SAIM puede diferir de los scripts de referencia] → Habilitar el mapeo PMP y de horas solo después de confirmar la respuesta autenticada; registrar campos no reconocidos como errores de mapeo.
- [Credencial comprometida en telemetría] → Redactar encabezados y valores sensibles en logs, auditoría y respuestas.
- [Ejecuciones concurrentes] → Serializar la sincronización y proteger la actualización del corte con transacción y bloqueo lógico.
- [El programador depende del entorno de despliegue] → Probar el disparador configurado en staging y conservar ejecución manual administrativa para recuperación.

## Migration Plan

1. Aplicar migraciones que creen tablas PMP sin modificar ni borrar tablas de eventos manuales.
2. Desplegar el importador, ejecutar la carga exclusiva de `añadidos/JOSE.xlsx` y revisar sus errores y reconciliación.
3. Habilitar el tablero PMP para validar los totales de Fase 1; solo una aprobación explícita habilita la configuración SAIM.
4. Desplegar la administración segura de token, configurar el programador de 7:00 a. m. Colombia y ejecutar una primera sincronización controlada.
5. Retirar la creación manual de la navegación y servicio, comprobando que los históricos continúan consultables.

Rollback: deshabilitar el programador SAIM y restaurar la versión anterior de la aplicación; las tablas PMP, importaciones, ejecuciones y snapshots permanecen para auditoría. Nunca se borran los registros históricos manuales ni el último corte PMP exitoso como parte del rollback.

## Open Questions

- La clasificación exacta que identifica una orden PMP en SAIM y el campo de horas-hombre planeadas se confirmarán al disponer de un token válido; el diseño los encapsula como configuración de mapeo para no cambiar los contratos de comportamiento.
