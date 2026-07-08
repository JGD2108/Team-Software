import csv
from pathlib import Path

from openpyxl import Workbook


SRC = Path("samples/INDICADORES MTTO TEAM B_QUILLA - TIEMPO MTTO VS PARETO (1).csv")
OUT = Path("samples/primera_carga_mantenimiento.xlsx")
REQUIRED = ["FECHA", "LINEA", "TURNO", "EQUIPO", "DAÑO", "RAZON", "TIEMPO", "FRECUENCIA", "AÑO", "MES"]


def fix_header(value: str) -> str:
    return value.strip().replace("DAÃ‘O", "DAÑO").replace("AÃ‘O", "AÑO")


def main() -> None:
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Historico")
    ws.append(REQUIRED)
    count = 0

    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [fix_header(h) for h in next(reader)]
        positions = [header.index(col) for col in REQUIRED]

        for row in reader:
            values = [(row[i] if i < len(row) else "") for i in positions]
            payload = dict(zip(REQUIRED, values, strict=True))
            equipment = payload["EQUIPO"].strip()
            is_total = equipment.upper().endswith(" TOTAL") or equipment.upper() == "TOTAL"
            if (
                payload["FECHA"].strip()
                and payload["LINEA"].strip()
                and equipment
                and payload["DAÑO"].strip()
                and payload["RAZON"].strip()
                and not is_total
            ):
                ws.append(values)
                count += 1

    wb.save(OUT)
    print(f"{OUT} ({count} filas)")


if __name__ == "__main__":
    main()
