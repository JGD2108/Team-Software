# Añadidos para la integración PMP / SAIM

Esta carpeta contiene los insumos entregados para implementar la integración por fases:

- `JOSE.xlsx`: carga histórica obligatoria para la Fase 1.
- `saim_ordenes_completo.gs`: script de consulta completa de órdenes y configuración del token.
- `saim_solicitudes_base.gs`: script de consulta de solicitudes para la hoja `BASEST`.
- `saim_ordenes_cumplimiento.gs`: script de consulta de órdenes y datos de cumplimiento para `BASEAPI` y `BD_SAIM`.

Los scripts son una referencia de Google Apps Script. La aplicación implementará su equivalente en el backend, sin almacenar el token en el código ni en esta carpeta.

Nota: el usuario proporcionó dos copias idénticas de `exportarDatosDeApiConPaginacion()`; se conserva una única copia canónica en `saim_ordenes_cumplimiento.gs`.
