# Arquitectura Del MVP

## Producto

Aplicación interna para reemplazar el proceso manual de consolidación Excel en mantenimiento industrial. El foco del MVP es carga manual `.xlsx`, validación, histórico, trazabilidad, corrección controlada, dashboards y PDF gerencial para administradores.

No incluye IoT, mantenimiento predictivo, repuestos, órdenes de trabajo completas, app móvil nativa ni integración automática con el sistema externo.

## Stack

- Frontend: React + Vite + TypeScript.
- Backend: FastAPI + SQLAlchemy.
- Base de datos: PostgreSQL en Docker; SQLite como fallback local para pruebas rápidas.
- Migraciones: Alembic.
- Excel: pandas + openpyxl.
- PDF: ReportLab.
- Gráficos: Recharts.
- Infra local: Docker Compose.

La elección prioriza rapidez de MVP, bajo acoplamiento y despliegue sencillo. FastAPI permite validar y procesar Excel con pandas sin crear una capa adicional de servicios.

## Flujo De Datos

```text
Usuario -> Login -> Carga .xlsx
  -> Validación de estructura y hoja
  -> Guardado del archivo original
  -> raw_maintenance_events + validation_errors
  -> Correcciones controladas con catálogos existentes
  -> Confirmación de carga
  -> maintenance_events
  -> Dashboard / Calidad / PDF
```

## Capas

- Raw: `uploaded_files`, `raw_maintenance_events`, `validation_errors`.
- Clean: `maintenance_events`, `production_lines`, `equipment`, `shifts`.
- Analytics: consultas agregadas sobre `maintenance_events`.
- Auditoría: `audit_logs`, `report_exports`.

## Permisos

- Usuario planta: inicia sesión, carga Excel, revisa estado, corrige registros con catálogos existentes, confirma cargas listas y ve dashboards.
- Administrador: todo lo anterior más gestión de usuarios, líneas, equipos, activación/desactivación, auditoría y generación/descarga de PDF.

## Modelo De Base De Datos

Las tablas implementadas están en `backend/app/models/entities.py` y en la migración Alembic inicial:

- `users`
- `production_lines`
- `equipment`
- `shifts`
- `uploaded_files`
- `raw_maintenance_events`
- `maintenance_events`
- `validation_errors`
- `audit_logs`
- `report_exports`

## Endpoints Principales

- `POST /auth/login`
- `GET /auth/me`
- `GET /users`
- `POST /users`
- `PATCH /users/{id}`
- `PATCH /users/{id}/activate`
- `PATCH /users/{id}/deactivate`
- `GET /production-lines`
- `POST /production-lines`
- `PATCH /production-lines/{id}`
- `PATCH /production-lines/{id}/activate`
- `PATCH /production-lines/{id}/deactivate`
- `GET /equipment`
- `POST /equipment`
- `PATCH /equipment/{id}`
- `PATCH /equipment/{id}/activate`
- `PATCH /equipment/{id}/deactivate`
- `GET /shifts`
- `GET /catalog-stats`
- `POST /uploads`
- `GET /uploads`
- `GET /uploads/{id}/preview`
- `GET /uploads/{id}/errors`
- `POST /uploads/{id}/confirm`
- `POST /uploads/{id}/reject`
- `GET /corrections/pending`
- `PATCH /raw-events/{id}/correction`
- `GET /dashboard/summary`
- `GET /dashboard/filters`
- `GET /data-quality/summary`
- `GET /data-quality/pending-records`
- `GET /audit-logs`
- `POST /reports/management-pdf`
- `GET /reports`
- `GET /reports/{id}/download`

## Validación Excel

Columnas obligatorias:

`FECHA`, `LINEA`, `TURNO`, `EQUIPO`, `DAÑO`, `RAZON`, `TIEMPO`, `FRECUENCIA`, `AÑO`, `MES`.

El sistema detecta automáticamente la hoja que contiene esas columnas. Si faltan, bloquea la carga. Si hay columnas extra, las ignora y registra advertencia.

Errores bloqueantes:

- Fecha inválida.
- Línea vacía o no reconocida.
- Equipo vacío, `error` o no reconocido.
- Daño o razón vacíos.
- Tiempo inválido o negativo.
- Frecuencia inválida o menor a 1.

Advertencias:

- Turno vacío.
- Año o mes no coinciden con fecha.
- Equipo asociado a línea distinta.
- Posible duplicado por hash de evento.

## Pantallas

- Inicio: última carga, pendientes, errores abiertos, tiempo perdido y acceso rápido a carga.
- Cargar archivo: subida `.xlsx`, validación y vista previa.
- Cargas: histórico de archivos y estados.
- Correcciones pendientes: registros bloqueantes corregibles.
- Dashboard: KPIs, Pareto, tiempo por mes, línea, equipo, daño, razón, turno y comparación tiempo vs frecuencia.
- Calidad de datos: errores, advertencias, pendientes, registros corregidos y porcentaje de calidad.
- Equipos: búsqueda, creación, edición y activación/desactivación para admin.
- Líneas: búsqueda, creación, edición y activación/desactivación para admin.
- Reportes: filtros y generación/descarga PDF solo admin.
- Usuarios: creación, cambio de rol y activación/desactivación solo admin.

## Siguiente Fase Recomendada

- Aprobación formal de nuevos equipos/líneas detectados como flujo separado.
- Catálogos normalizados para `DAÑO` y `RAZON`.
- Importación asistida de archivos históricos grandes por lotes.
- CI/CD con despliegue a Render, Railway, Fly.io o Azure.
- Observabilidad básica: métricas de API, logs estructurados y alertas de fallos de carga.
- Exportaciones Excel gerenciales adicionales.
