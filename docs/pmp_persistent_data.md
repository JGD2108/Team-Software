# PMP: carga persistente de JOSE.xlsx

`JOSE.xlsx` es una fuente de carga inicial, no un archivo servido ni una dependencia de las solicitudes del tablero. La carga explícita persiste las órdenes válidas, sus fechas planeadas, los diagnósticos de filas inválidas y la reconciliación esperada. Las rutas `/pmp/dashboard`, `/pmp/orders` y `/pmp/imports/latest` leen únicamente tablas PMP.

La carga es idempotente por hash SHA-256 de la fuente: repetirla con el mismo archivo reutiliza la misma importación, actualiza la proyección persistida si hace falta y no duplica órdenes, diagnósticos ni historial sin cambios.

## Aplicación inicial en un entorno remoto

No ejecute estos pasos contra producción hasta que se haya aprobado el despliegue de backend. Con una sesión que tenga la misma variable `DATABASE_URL` del backend remoto, desde `backend`:

```powershell
alembic upgrade head
python -m scripts.import_pmp_jose
```

El primer comando crea la proyección de fecha, los índices y el campo de reconciliación; no borra ni modifica eventos históricos de fallas. El segundo comando realiza la única lectura operativa del Excel y puede repetirse con seguridad. Para una copia aprobada fuera de la ruta predeterminada:

```powershell
python -m scripts.import_pmp_jose --source 'C:\ruta\aprobada\JOSE.xlsx'
```

La salida JSON debe indicar, para la fuente actual, `total_rows: 1082`, `valid_rows: 1009`, `invalid_rows: 73`, `reconciliation.matches: true`, `1009` órdenes persistidas y `53874.0` minutos planeados. Revise las diferencias y los diagnósticos antes de aprobar la importación. No habilite SAIM como parte de este procedimiento.

## Consultas operativas

Los filtros `area`, `status`, `date_from` y `date_to` se ejecutan contra `pmp_orders` y `pmp_areas`; las fechas son inclusivas. `as_of_date` se conserva temporalmente como compatibilidad y no puede mezclarse con el rango. Los índices compuestos cubren área/estado/fecha y la ordenación paginada.
