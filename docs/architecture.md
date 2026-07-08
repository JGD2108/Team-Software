# Arquitectura Del MVP

## Producto

Aplicación interna para reemplazar el proceso manual de consolidación Excel en mantenimiento industrial. El foco del MVP es carga manual `.xlsx`, validación, trazabilidad, corrección controlada, dashboards y PDF gerencial para administradores.

## Stack

- Frontend: React + Vite + TypeScript.
- Backend: FastAPI + SQLAlchemy.
- Base de datos: PostgreSQL en Docker; SQLite como fallback local para pruebas rápidas.
- Excel: pandas + openpyxl.
- PDF: ReportLab.
- Gráficos: Recharts.

## Flujo De Datos

```text
Usuario -> Login -> Carga .xlsx
  -> Validación de estructura
  -> Guardado archivo original
  -> raw_maintenance_events + validation_errors
  -> Correcciones controladas
  -> Confirmación
  -> maintenance_events
  -> Dashboard / Calidad / PDF
```

## Capas

- Raw: `uploaded_files`, `raw_maintenance_events`, `validation_errors`.
- Clean: `maintenance_events`, `production_lines`, `equipment`, `shifts`.
- Analytics: endpoints agregados sobre `maintenance_events`.

## Permisos

- Usuario planta: carga, revisa, corrige con catálogos existentes, confirma cargas y ve dashboards.
- Administrador: todo lo anterior más usuarios, catálogos, rechazo de cargas y PDF.

## Modelo De Base De Datos

Las tablas implementadas están en `backend/app/models/entities.py`:

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

## Endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET/POST /users`
- `GET/POST/PATCH /production-lines`
- `GET/POST/PATCH /equipment`
- `POST /uploads`
- `GET /uploads`
- `GET /uploads/{id}/preview`
- `GET /uploads/{id}/errors`
- `POST /uploads/{id}/confirm`
- `POST /uploads/{id}/reject`
- `GET /corrections/pending`
- `PATCH /raw-events/{id}/correction`
- `GET /dashboard/summary`
- `GET /data-quality/summary`
- `POST /reports/management-pdf`
- `GET /reports`
- `GET /reports/{id}/download`

## Validación Excel

Columnas obligatorias:

`FECHA`, `LINEA`, `TURNO`, `EQUIPO`, `DAÑO`, `RAZON`, `TIEMPO`, `FRECUENCIA`, `AÑO`, `MES`.

El sistema detecta la hoja que contiene esas columnas. Si faltan, bloquea la carga. Si hay columnas extra, las ignora y registra advertencia.

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

## Siguiente Fase Recomendada

- Migraciones Alembic formales.
- Aprobación explícita de nuevos equipos/líneas detectados.
- Estandarización de daño/razón con catálogos sugeridos.
- Auditoría más granular de cambios campo a campo.
- Exportaciones Excel adicionales.
