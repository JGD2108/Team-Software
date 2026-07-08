# MVP Mantenimiento Industrial

MVP web para carga manual de Excel, validación, trazabilidad, dashboards y reportes PDF de mantenimiento.

## Usuarios Seed

- Admin: `admin@mantenimiento.local` / `Admin123!`
- Planta: `planta@mantenimiento.local` / `Planta123!`

## Ejecutar Con Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8001
- API docs: http://localhost:8001/docs

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
python -m pytest
```

## Documentación

Ver [docs/architecture.md](docs/architecture.md).
