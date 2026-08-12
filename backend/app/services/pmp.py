"""Phase 1 PMP import, reconciliation, metrics, and capacity domain services."""

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models import PmpArea, PmpImport, PmpImportError, PmpOrder, PmpOrderHistory, PmpPersonnel, PmpWeeklySchedule


JOSE_FILENAME = "JOSE.xlsx"
# JOSE.xlsx has five identical "Activo" headers.  These positions are the
# contract; never infer them from the repeated header labels.
JOSE_POSITIONS = {"external_id": 10, "area": 8, "planned_minutes": 14, "state": 15}
ALLOWED_STATES = {"ABIERTO": "pending", "FINALIZADO": "finalized"}
SHIFT_NAMES = {"1", "2", "3"}


def default_jose_path() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "añadidos" / JOSE_FILENAME


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _payload(row: tuple[Any, ...]) -> str:
    return json.dumps({str(index): value for index, value in enumerate(row)}, default=str, ensure_ascii=False)


def _totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_area: dict[str, dict[str, Any]] = defaultdict(lambda: {"orders": 0, "planned_minutes": 0.0, "finalized_orders": 0, "pending_orders": 0, "finalized_minutes": 0.0, "pending_minutes": 0.0})
    for row in rows:
        target = by_area[row["area"]]
        target["orders"] += 1
        target["planned_minutes"] += row["planned_minutes"]
        target[f"{row['status']}_orders"] += 1
        target[f"{row['status']}_minutes"] += row["planned_minutes"]
    total = {"orders": len(rows), "planned_minutes": sum(row["planned_minutes"] for row in rows), "finalized_orders": sum(row["status"] == "finalized" for row in rows), "pending_orders": sum(row["status"] == "pending" for row in rows)}
    total["finalized_minutes"] = sum(row["planned_minutes"] for row in rows if row["status"] == "finalized")
    total["pending_minutes"] = sum(row["planned_minutes"] for row in rows if row["status"] == "pending")
    return {"global": total, "by_area": dict(sorted(by_area.items()))}


def _parse_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    if path.name != JOSE_FILENAME:
        raise ValueError("La fuente inicial permitida es exclusivamente JOSE.xlsx")
    worksheet = load_workbook(path, read_only=True, data_only=True).active
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        external_id = _text(row[JOSE_POSITIONS["external_id"]])
        area = _text(row[JOSE_POSITIONS["area"]]).upper()
        source_state = _text(row[JOSE_POSITIONS["state"]]).upper()
        raw_minutes = row[JOSE_POSITIONS["planned_minutes"]]
        error: tuple[str, str, str] | None = None
        if not external_id:
            error = ("external_id", "missing_external_id", "La orden no tiene identificador externo utilizable")
        elif not area:
            error = ("area", "missing_area", "Especialidad es obligatoria para el área PMP")
        elif source_state not in ALLOWED_STATES:
            error = ("state", "invalid_state", "Estado debe ser Abierto o Finalizado")
        else:
            try:
                planned_minutes = float(raw_minutes)
                if planned_minutes <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                error = ("planned_minutes", "invalid_planned_minutes", "TiempoPlaneado debe ser numérico y mayor que cero")
            else:
                if external_id in seen_ids:
                    error = ("external_id", "duplicate_external_id", "Identificador externo repetido en JOSE.xlsx")
        if error:
            invalid.append({"row_number": row_number, "field_name": error[0], "error_code": error[1], "error_message": error[2], "raw_payload_json": _payload(row)})
            continue
        seen_ids.add(external_id)
        valid.append({"row_number": row_number, "external_id": external_id, "area": area, "status": ALLOWED_STATES[source_state], "planned_minutes": planned_minutes, "raw_payload_json": _payload(row)})
    return valid, invalid, worksheet.max_row - 1


def import_jose_workbook(db: Session, path: Path | None = None) -> PmpImport:
    source = path or default_jose_path()
    content_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    existing = db.query(PmpImport).filter(PmpImport.source_hash == content_hash).order_by(PmpImport.id.desc()).first()
    if existing:
        return existing
    valid_rows, invalid_rows, total_rows = _parse_rows(source)
    imported = PmpImport(source_filename=JOSE_FILENAME, source_hash=content_hash, status="completed", total_rows=total_rows, valid_rows=len(valid_rows), invalid_rows=len(invalid_rows), reconciled_at=datetime.utcnow())
    db.add(imported)
    db.flush()
    areas: dict[str, PmpArea] = {}
    for name in sorted({row["area"] for row in valid_rows}):
        area = db.query(PmpArea).filter(PmpArea.name == name).first()
        if not area:
            area = PmpArea(name=name)
            db.add(area)
            db.flush()
        areas[name] = area
    for row in valid_rows:
        order = PmpOrder(external_id=row["external_id"], pmp_area_id=areas[row["area"]].id, status=row["status"], planned_minutes=row["planned_minutes"], source="excel", source_row_number=row["row_number"], pmp_import_id=imported.id, raw_payload_json=row["raw_payload_json"])
        db.add(order)
        db.flush()
        db.add(PmpOrderHistory(pmp_order_id=order.id, action="excel_import", after_json=json.dumps({"import_id": imported.id, "row_number": row["row_number"]})))
    for row in invalid_rows:
        db.add(PmpImportError(pmp_import_id=imported.id, **row))
    db.commit()
    return imported


def import_summary(db: Session, imported: PmpImport) -> dict[str, Any]:
    errors = db.query(PmpImportError).filter(PmpImportError.pmp_import_id == imported.id).order_by(PmpImportError.row_number).all()
    reconciliation = reconcile_import(db, imported)
    return {"id": imported.id, "source_filename": imported.source_filename, "status": imported.status, "total_rows": imported.total_rows, "valid_rows": imported.valid_rows, "invalid_rows": imported.invalid_rows, "approved_at": imported.approved_at, "reconciliation": reconciliation, "errors": [{"row_number": item.row_number, "field_name": item.field_name, "code": item.error_code, "message": item.error_message} for item in errors]}


def reconcile_import(db: Session, imported: PmpImport) -> dict[str, Any]:
    # Expected data is reconstructed from the immutable workbook, while actual
    # data is restricted to this import.  This makes a mismatch visible.
    expected_rows, _, _ = _parse_rows(default_jose_path())
    actual_rows = db.query(PmpOrder, PmpArea).join(PmpArea).filter(PmpOrder.pmp_import_id == imported.id, PmpOrder.is_active.is_(True)).all()
    actual = [{"area": area.name, "status": order.status, "planned_minutes": order.planned_minutes} for order, area in actual_rows]
    expected = _totals(expected_rows)
    persisted = _totals(actual)
    differences = {"global": {}, "by_area": {}}
    for key in expected["global"]:
        delta = persisted["global"].get(key, 0) - expected["global"].get(key, 0)
        if delta:
            differences["global"][key] = delta
    for area in sorted(set(expected["by_area"]) | set(persisted["by_area"])):
        area_differences = {}
        for key in set(expected["by_area"].get(area, {})) | set(persisted["by_area"].get(area, {})):
            delta = persisted["by_area"].get(area, {}).get(key, 0) - expected["by_area"].get(area, {}).get(key, 0)
            if delta:
                area_differences[key] = delta
        if area_differences:
            differences["by_area"][area] = area_differences
    return {"matches": not differences["global"] and not differences["by_area"], "expected": expected, "persisted": persisted, "differences": differences}


def dashboard_metrics(db: Session, area_name: str | None = None) -> dict[str, Any]:
    query = db.query(PmpOrder, PmpArea).join(PmpArea).filter(PmpOrder.is_active.is_(True))
    if area_name:
        query = query.filter(PmpArea.name == area_name.upper())
    rows = [{"area": area.name, "status": order.status, "planned_minutes": order.planned_minutes} for order, area in query.all()]
    totals = _totals(rows)
    for item in totals["by_area"].values():
        item["compliance_percent"] = round(100 * item["finalized_orders"] / item["orders"], 2) if item["orders"] else 0.0
        item["compliant"] = item["compliance_percent"] > 90
    overall = totals["global"]
    overall["compliance_percent"] = round(100 * overall["finalized_orders"] / overall["orders"], 2) if overall["orders"] else 0.0
    overall["compliant"] = overall["compliance_percent"] > 90
    overall["traffic_light"] = "green" if overall["compliant"] else "red"
    return {**totals, "alerts": [] if overall["compliant"] else [{"code": "pmp_compliance_below_target", "message": "El cumplimiento PMP debe ser estrictamente mayor que 90 %."}]}


def capacity_metrics(db: Session, week_start: date, area_name: str | None = None) -> list[dict[str, Any]]:
    schedules = db.query(PmpWeeklySchedule, PmpArea).join(PmpArea).filter(PmpWeeklySchedule.week_start == week_start)
    if area_name:
        schedules = schedules.filter(PmpArea.name == area_name.upper())
    capacity: dict[tuple[str, str], float] = defaultdict(float)
    for schedule, area in schedules.all():
        capacity[(area.name, schedule.shift_name)] += schedule.available_minutes
    pending = dashboard_metrics(db, area_name)["by_area"]
    result = []
    for (area, shift), available_minutes in sorted(capacity.items()):
        # Pending workload is allocated visibly by the selected shift.  The
        # UI can schedule it across shifts by entering capacity for each one.
        pending_minutes = pending.get(area, {}).get("pending_minutes", 0.0)
        gap_minutes = pending_minutes - available_minutes
        fte_required = max(0.0, gap_minutes / available_minutes) if available_minutes else (1.0 if pending_minutes else 0.0)
        result.append({"area": area, "shift": shift, "week_start": week_start, "available_minutes": available_minutes, "pending_minutes": pending_minutes, "gap_minutes": gap_minutes, "fte_required": round(fte_required, 2), "alert": gap_minutes > 0})
    return result


def validate_schedule(shift_name: str, available_minutes: float) -> None:
    if shift_name not in SHIFT_NAMES:
        raise ValueError("El turno PMP debe ser 1, 2 o 3")
    if available_minutes < 0:
        raise ValueError("Los minutos disponibles no pueden ser negativos")
