from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import AuditLog, Equipment, MaintenanceEvent, ProductionLine, Shift, UploadedFile, User, ValidationError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
quality_router = APIRouter(prefix="/data-quality", tags=["data-quality"])
audit_router = APIRouter(prefix="/audit-logs", tags=["audit"])


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

    date_range = q.with_entities(
        func.min(MaintenanceEvent.event_date),
        func.max(MaintenanceEvent.event_date),
    ).first()

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

    equipment_rows = (
        q.join(Equipment)
        .with_entities(
            Equipment.name.label("name"),
            func.sum(MaintenanceEvent.downtime_minutes).label("downtime"),
            func.sum(MaintenanceEvent.frequency).label("frequency"),
            func.count(MaintenanceEvent.id).label("events"),
        )
        .group_by(Equipment.name)
        .order_by(func.sum(MaintenanceEvent.downtime_minutes).desc())
        .limit(12)
        .all()
    )
    equipment_time = [{"name": row.name, "value": float(row.downtime or 0)} for row in equipment_rows]
    equipment_freq = pairs(Equipment, Equipment.name, "frequency")
    lines = pairs(ProductionLine, ProductionLine.name, "downtime")
    shifts = pairs(Shift, Shift.name, "downtime")
    reasons = q.with_entities(MaintenanceEvent.reason_description.label("name"), func.sum(MaintenanceEvent.downtime_minutes).label("value")).group_by(MaintenanceEvent.reason_description).order_by(func.sum(MaintenanceEvent.downtime_minutes).desc()).limit(10).all()
    months = q.with_entities(MaintenanceEvent.year, MaintenanceEvent.month, func.sum(MaintenanceEvent.downtime_minutes).label("downtime"), func.count(MaintenanceEvent.id).label("events")).group_by(MaintenanceEvent.year, MaintenanceEvent.month).order_by(MaintenanceEvent.year, MaintenanceEvent.month).all()
    days = (
        q.with_entities(
            MaintenanceEvent.event_date.label("date"),
            func.sum(MaintenanceEvent.downtime_minutes).label("downtime"),
            func.sum(MaintenanceEvent.frequency).label("frequency"),
            func.count(MaintenanceEvent.id).label("events"),
        )
        .group_by(MaintenanceEvent.event_date)
        .order_by(MaintenanceEvent.event_date)
        .all()
    )
    pareto = []
    running = 0.0
    for item in equipment_time:
        running += item["value"]
        pareto.append({**item, "cumulative": round((running / total_minutes * 100) if total_minutes else 0, 2)})

    critical_equipment = []
    running = 0.0
    for row in equipment_rows:
        downtime = float(row.downtime or 0)
        frequency = float(row.frequency or 0)
        running += downtime
        critical_equipment.append({
            "name": row.name,
            "downtime": downtime,
            "frequency": frequency,
            "events": int(row.events or 0),
            "mttr": round(downtime / frequency, 1) if frequency else 0,
            "percentage": round((downtime / total_minutes * 100) if total_minutes else 0, 2),
            "cumulative": round((running / total_minutes * 100) if total_minutes else 0, 2),
        })

    frequency_by_equipment = {row.name: float(row.frequency or 0) for row in equipment_rows}
    peak_day = max(days, key=lambda row: float(row.downtime or 0), default=None)
    top_four_minutes = sum(item["value"] for item in equipment_time[:4])
    top_four_percentage = round((top_four_minutes / total_minutes * 100) if total_minutes else 0, 1)
    mttr = round(float(total_minutes or 0) / float(total_frequency or 0), 1) if total_frequency else 0
    critical_name = equipment_time[0]["name"] if equipment_time else "Sin datos"
    critical_line = lines[0]["name"] if lines else "Sin datos"

    return {
        "kpis": {
            "total_minutes": float(total_minutes or 0),
            "total_hours": round(float(total_minutes or 0) / 60, 2),
            "total_events": total_events,
            "total_frequency": float(total_frequency or 0),
            "mttr": mttr,
            "critical_equipment": critical_name,
            "critical_line": critical_line,
            "validated_records": total_events,
            "top_four_percentage": top_four_percentage,
        },
        "period": {
            "date_from": date_range[0].isoformat() if date_range and date_range[0] else None,
            "date_to": date_range[1].isoformat() if date_range and date_range[1] else None,
        },
        "downtime_by_month": [{"name": f"{r.year}-{int(r.month):02d}", "downtime": float(r.downtime or 0), "events": int(r.events)} for r in months],
        "daily_trend": [{"name": r.date.isoformat(), "downtime": float(r.downtime or 0), "frequency": float(r.frequency or 0), "events": int(r.events)} for r in days],
        "downtime_by_line": lines,
        "top_equipment_downtime": equipment_time,
        "top_equipment_frequency": equipment_freq,
        "pareto": pareto,
        "downtime_vs_frequency": [{"name": a["name"], "downtime": a["value"], "frequency": frequency_by_equipment.get(a["name"], 0)} for a in equipment_time],
        "critical_equipment": critical_equipment,
        "top_reasons": [{"name": r.name, "value": float(r.value or 0)} for r in reasons],
        "by_shift": shifts,
        "insights": {
            "highest_downtime": {
                "name": critical_name,
                "minutes": equipment_time[0]["value"] if equipment_time else 0,
                "percentage": critical_equipment[0]["percentage"] if critical_equipment else 0,
            },
            "highest_frequency": {
                "name": equipment_freq[0]["name"] if equipment_freq else "Sin datos",
                "frequency": equipment_freq[0]["value"] if equipment_freq else 0,
            },
            "peak_day": {
                "date": peak_day.date.isoformat() if peak_day else None,
                "minutes": float(peak_day.downtime or 0) if peak_day else 0,
                "events": int(peak_day.events or 0) if peak_day else 0,
            },
            "top_four_minutes": top_four_minutes,
            "top_four_percentage": top_four_percentage,
        },
    }


@router.get("/filters")
def dashboard_filters(_: User = Depends(current_user), db: Session = Depends(get_db)):
    years = [row[0] for row in db.query(MaintenanceEvent.year).distinct().order_by(MaintenanceEvent.year).all()]
    months = [row[0] for row in db.query(MaintenanceEvent.month).distinct().order_by(MaintenanceEvent.month).all()]
    return {
        "years": years,
        "months": months,
        "lines": [{"id": line.id, "name": line.name} for line in db.query(ProductionLine).filter(ProductionLine.is_active.is_(True)).order_by(ProductionLine.name).all()],
        "equipment": [{"id": item.id, "name": item.name, "production_line_id": item.production_line_id} for item in db.query(Equipment).filter(Equipment.is_active.is_(True)).order_by(Equipment.name).all()],
        "shifts": [{"id": shift.id, "name": shift.name} for shift in db.query(Shift).filter(Shift.is_active.is_(True)).order_by(Shift.name).all()],
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


@quality_router.get("/pending-records")
def quality_pending_records(_: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(ValidationError)
        .join(UploadedFile, UploadedFile.id == ValidationError.uploaded_file_id)
        .filter(UploadedFile.status != "rejected", ValidationError.status == "open")
        .order_by(ValidationError.created_at.desc())
        .limit(500)
        .all()
    )
    return [
        {
            "id": row.id,
            "uploaded_file_id": row.uploaded_file_id,
            "raw_event_id": row.raw_event_id,
            "field_name": row.field_name,
            "error_type": row.error_type,
            "severity": row.severity,
            "message": row.error_message,
        }
        for row in rows
    ]


@audit_router.get("")
def list_audit_logs(limit: int = 200, _: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 1000)).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "action": row.action,
            "before_json": row.before_json,
            "after_json": row.after_json,
            "created_at": row.created_at,
        }
        for row in rows
    ]
