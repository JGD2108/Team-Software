# MVP Mantenimiento Industrial

Aplicación web interna para reemplazar el flujo manual de consolidación Excel en mantenimiento industrial. El MVP cubre carga manual `.xlsx`, validación, trazabilidad, correcciones controladas, dashboards gerenciales, calidad de datos y reportes PDF para administradores.

## Usuarios Seed

- Admin: `admin@mantenimiento.local` / `Admin123!`
- Planta: `planta@mantenimiento.local` / `Planta123!`

## Ejecutar Con Docker

```bash
docker compose up -d --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8001
- API docs: http://localhost:8001/docs

La base de datos PostgreSQL corre dentro de Docker sin publicar el puerto `5432`, para evitar conflictos con instalaciones locales.

## Ejecutar Local Sin Docker

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Crear Excel De Ejemplo

```bash
pip install openpyxl
python scripts_create_sample_excel.py
```

El archivo se genera en `samples/carga_mantenimiento_ejemplo.xlsx`.

## Pruebas

```bash
cd backend
python -m pytest app/tests

cd ../frontend
npm run build
```

## Migraciones

El esquema inicial está documentado en Alembic:

```bash
cd backend
alembic upgrade head
```

En el modo Docker actual, la app crea tablas al iniciar para facilitar el MVP local.

## Documentación

Ver [docs/architecture.md](docs/architecture.md).
