from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import Equipment, MaintenanceEvent, ProductionLine, Shift, UploadedFile, User, ValidationError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
quality_router = APIRouter(prefix="/data-quality", tags=["data-quality"])


def _filtered(db: Session, date_from: date | None, date_to: date | None, year: int | None, month: int | None, production_line_id: int | None, equipment_id: int | None, shift_id: int | None):
    q = db.query(MaintenanceEvent)
    if date_from:
        q = q.filter(MaintenanceEvent.event_date >= date_from)
    if date_to:
        q = q.filter(MaintenanceEvent.event_date <= date_to)
    if year:
        q = q.filter(MaintenanceEvent.year == year)
    if month:
        q = q.filter(MaintenanceEvent.month == month)
    if production_line_id:
        q = q.filter(MaintenanceEvent.production_line_id == production_line_id)
    if equipment_id:
        q = q.filter(MaintenanceEvent.equipment_id == equipment_id)
    if shift_id:
        q = q.filter(MaintenanceEvent.shift_id == shift_id)
    return q


@router.get("/summary")
def dashboard_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    year: int | None = None,
    month: int | None = None,
    production_line_id: int | None = None,
    equipment_id: int | None = None,
    shift_id: int | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    q = _filtered(db, date_from, date_to, year, month, production_line_id, equipment_id, shift_id)
    total_minutes = q.with_entities(func.coalesce(func.sum(MaintenanceEvent.downtime_minutes), 0)).scalar()
    total_events = q.count()
    total_frequency = q.with_entities(func.coalesce(func.sum(MaintenanceEvent.frequency), 0)).scalar()

    def pairs(model, field, metric="downtime"):
        value = func.sum(MaintenanceEvent.downtime_minutes if metric == "downtime" else MaintenanceEvent.frequency)
        rows = (
            q.join(model)
            .with_entities(field.label("name"), value.label("value"))
            .group_by(field)
            .order_by(value.desc())
            .limit(10)
            .all()
        )
        return [{"name": r.name or "Sin turno", "value": float(r.value or 0)} for r in rows]

    equipment_time = pairs(Equipment, Equipment.name, "downtime")
    equipment_freq = pairs(Equipment, Equipment.name, "frequency")
    lines = pairs(ProductionLine, ProductionLine.name, "downtime")
    shifts = pairs(Shift, Shift.name, "downtime")
    damages = q.with_entities(MaintenanceEvent.damage_description.label("name"), func.sum(MaintenanceEvent.downtime_minutes).label("value")).group_by(MaintenanceEvent.damage_description).order_by(func.sum(MaintenanceEvent.downtime_minutes).desc()).limit(10).all()
    reasons = q.with_entities(MaintenanceEvent.reason_description.label("name"), func.sum(MaintenanceEvent.downtime_minutes).label("value")).group_by(MaintenanceEvent.reason_description).order_by(func.sum(MaintenanceEvent.downtime_minutes).desc()).limit(10).all()
    months = q.with_entities(MaintenanceEvent.year, MaintenanceEvent.month, func.sum(MaintenanceEvent.downtime_minutes).label("downtime"), func.count(MaintenanceEvent.id).label("events")).group_by(MaintenanceEvent.year, MaintenanceEvent.month).order_by(MaintenanceEvent.year, MaintenanceEvent.month).all()
    pareto = []
    running = 0.0
    for item in equipment_time:
        running += item["value"]
        pareto.append({**item, "cumulative": round((running / total_minutes * 100) if total_minutes else 0, 2)})

    return {
        "kpis": {
            "total_minutes": float(total_minutes or 0),
            "total_hours": round(float(total_minutes or 0) / 60, 2),
            "total_events": total_events,
            "total_frequency": float(total_frequency or 0),
            "critical_equipment": equipment_time[0]["name"] if equipment_time else "Sin datos",
            "critical_line": lines[0]["name"] if lines else "Sin datos",
            "validated_records": total_events,
        },
        "downtime_by_month": [{"name": f"{r.year}-{int(r.month):02d}", "downtime": float(r.downtime or 0), "events": int(r.events)} for r in months],
        "downtime_by_line": lines,
        "top_equipment_downtime": equipment_time,
        "top_equipment_frequency": equipment_freq,
        "pareto": pareto,
        "downtime_vs_frequency": [{"name": a["name"], "downtime": a["value"], "frequency": next((b["value"] for b in equipment_freq if b["name"] == a["name"]), 0)} for a in equipment_time],
        "top_damages": [{"name": r.name, "value": float(r.value or 0)} for r in damages],
        "top_reasons": [{"name": r.name, "value": float(r.value or 0)} for r in reasons],
        "by_shift": shifts,
    }


@quality_router.get("/summary")
def quality_summary(_: User = Depends(current_user), db: Session = Depends(get_db)):
    uploads = db.query(UploadedFile).count()
    pending = db.query(UploadedFile).filter(UploadedFile.status.in_(["pending_corrections", "ready_to_confirm", "uploaded"])).count()
    active_errors = db.query(ValidationError).join(UploadedFile, UploadedFile.id == ValidationError.uploaded_file_id).filter(UploadedFile.status != "rejected")
    errors = active_errors.filter(ValidationError.severity == "error", ValidationError.status == "open").count()
    warnings = active_errors.filter(ValidationError.severity == "warning").count()
    corrected = active_errors.filter(ValidationError.status == "resolved").count()
    total_rows = db.query(func.coalesce(func.sum(UploadedFile.total_rows), 0)).filter(UploadedFile.status != "rejected").scalar() or 0
    valid_rows = db.query(func.coalesce(func.sum(UploadedFile.valid_rows), 0)).filter(UploadedFile.status != "rejected").scalar() or 0
    quality = round((valid_rows / total_rows * 100) if total_rows else 100, 2)
    by_type = (
        db.query(ValidationError.error_type, func.count(ValidationError.id))
        .join(UploadedFile, UploadedFile.id == ValidationError.uploaded_file_id)
        .filter(UploadedFile.status != "rejected")
        .group_by(ValidationError.error_type)
        .all()
    )
    return {
        "uploads": uploads,
        "pending_uploads": pending,
        "open_errors": errors,
        "warnings": warnings,
        "corrected_records": corrected,
        "data_quality_percent": quality,
        "errors_by_type": [{"type": t, "count": c} for t, c in by_type],
    }
