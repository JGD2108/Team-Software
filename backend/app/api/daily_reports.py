import hashlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import Equipment, FailureMode, MaintenanceEvent, ProductionLine, Shift, User
from app.schemas.common import DailyReportIn
from app.services.audit import log_action
from app.services.normalization import normalize_report_text

router = APIRouter(prefix="/daily-reports", tags=["daily-reports"])
BOGOTA = ZoneInfo("America/Bogota")


def local_today():
    return datetime.now(BOGOTA).date()


def serialize_report(row):
    event, line, shift, equipment, failure_mode, reporter = row
    return {
        "id": event.id,
        "event_date": event.event_date,
        "production_line_id": event.production_line_id,
        "line_name": line.name,
        "area_code": equipment.area_code or line.code,
        "area_name": equipment.area_name or line.name,
        "process_code": equipment.process_code,
        "process_name": equipment.process_name,
        "shift_id": event.shift_id,
        "shift_name": shift.name,
        "equipment_id": event.equipment_id,
        "equipment_code": equipment.code,
        "equipment_name": equipment.name,
        "failure_mode_id": event.failure_mode_id,
        "failure_mode_name": failure_mode.name,
        "damage_description": event.damage_description,
        "reason_description": event.reason_description,
        "downtime_minutes": event.downtime_minutes,
        "frequency": event.frequency,
        "reported_by": reporter.name,
        "created_at": event.created_at,
    }


def report_query(db: Session):
    return (
        db.query(MaintenanceEvent, ProductionLine, Shift, Equipment, FailureMode, User)
        .join(ProductionLine, ProductionLine.id == MaintenanceEvent.production_line_id)
        .join(Shift, Shift.id == MaintenanceEvent.shift_id)
        .join(Equipment, Equipment.id == MaintenanceEvent.equipment_id)
        .join(FailureMode, FailureMode.id == MaintenanceEvent.failure_mode_id)
        .join(User, User.id == MaintenanceEvent.reported_by_user_id)
        .filter(MaintenanceEvent.source == "manual_report")
    )


@router.get("")
def list_daily_reports(
    report_date: date | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    target_date = report_date or local_today()
    rows = report_query(db).filter(MaintenanceEvent.event_date == target_date).order_by(MaintenanceEvent.created_at.desc()).all()
    return [serialize_report(row) for row in rows]


@router.post("", status_code=201)
def create_daily_report(payload: DailyReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    # PMP replaces manual failure capture.  Historical GET endpoints remain
    # available, but this legacy creation route must not add new events.
    raise HTTPException(status_code=410, detail="El registro manual de fallas fue retirado; consulte los históricos existentes")


def _legacy_create_daily_report(payload: DailyReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, payload.production_line_id)
    equipment = db.get(Equipment, payload.equipment_id)
    shift = db.get(Shift, payload.shift_id)
    failure_mode = db.get(FailureMode, payload.failure_mode_id)
    if not line or not line.is_active:
        raise HTTPException(status_code=400, detail="Selecciona un \u00e1rea / l\u00ednea activa")
    if not equipment or not equipment.is_active or equipment.production_line_id != line.id:
        raise HTTPException(status_code=400, detail="El activo no pertenece al \u00e1rea seleccionada")
    if not shift or not shift.is_active or shift.name not in {"1", "2", "3"}:
        raise HTTPException(status_code=400, detail="Selecciona el turno 1, 2 o 3")
    if not failure_mode or not failure_mode.is_active:
        raise HTTPException(status_code=400, detail="Selecciona un modo de falla activo")

    event_date = payload.event_date
    if event_date > local_today():
        raise HTTPException(status_code=400, detail="La fecha del reporte no puede ser futura")
    normalized_damage = normalize_report_text(payload.damage_description)
    normalized_reason = normalize_report_text(payload.reason_description)
    signature = f"{user.id}|{datetime.now(BOGOTA).isoformat()}|{payload.model_dump_json()}"
    event = MaintenanceEvent(
        uploaded_file_id=None,
        event_hash=hashlib.sha256(signature.encode("utf-8")).hexdigest(),
        event_date=event_date,
        production_line_id=line.id,
        shift_id=shift.id,
        equipment_id=equipment.id,
        failure_mode_id=failure_mode.id,
        reported_by_user_id=user.id,
        damage_description=normalized_damage,
        reason_description=normalized_reason,
        raw_damage_description=payload.damage_description.strip(),
        raw_reason_description=payload.reason_description.strip(),
        downtime_minutes=payload.downtime_minutes,
        frequency=float(payload.frequency),
        year=event_date.year,
        month=event_date.month,
        status="confirmed",
        source="manual_report",
    )
    db.add(event)
    db.flush()
    log_action(db, user, "maintenance_event", "daily_report_create", event.id, after={"failure_mode": failure_mode.name})
    db.commit()
    row = report_query(db).filter(MaintenanceEvent.id == event.id).one()
    return serialize_report(row)


@router.get("/suggestions")
def report_suggestions(
    field: str,
    q: str = "",
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if field not in {"damage", "reason"}:
        raise HTTPException(status_code=400, detail="Campo de sugerencia inv\u00e1lido")
    column = MaintenanceEvent.damage_description if field == "damage" else MaintenanceEvent.reason_description
    query = db.query(column.label("value")).filter(MaintenanceEvent.source == "manual_report")
    if q.strip():
        query = query.filter(func.lower(column).contains(q.strip().lower()))
    rows = query.distinct().order_by(column).limit(12).all()
    return [row.value for row in rows if row.value]
