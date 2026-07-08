from pathlib import Path

from openpyxl import Workbook

headers = ["FECHA", "LINEA", "TURNO", "EQUIPO", "DAÑO", "RAZON", "TIEMPO", "FRECUENCIA", "AÑO", "MES", "COLUMNA_EXTRA"]
rows = [
    ["2026-07-01", "Linea 1", "Turno A", "Bomba principal", "Fuga", "Sello desgastado", 45, 1, 2026, 7, "ignorar"],
    ["2026-07-01", "Linea 1", "Turno B", "Compresor 1", "Ruido", "Rodamiento", 30, 1, 2026, 7, "ignorar"],
    ["2026-07-02", "Linea 2", "", "Transportador A", "Atasco", "Material acumulado", 75, 2, 2026, 7, "ignorar"],
    ["2026-07-03", "Linea 2", "Turno C", "error", "Parada", "Sin clasificar", 20, 1, 2026, 7, "ignorar"],
    ["2026-07-04", "Linea nueva", "Turno A", "Equipo nuevo", "Falla", "Causa pendiente", 15, 1, 2026, 7, "ignorar"],
]

wb = Workbook()
ws = wb.active
ws.title = "Datos mantenimiento"
ws.append(headers)
for row in rows:
    ws.append(row)

Path("samples").mkdir(exist_ok=True)
wb.save("samples/carga_mantenimiento_ejemplo.xlsx")
print("samples/carga_mantenimiento_ejemplo.xlsx")
