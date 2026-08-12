from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.models import PmpArea, PmpImport, PmpPersonnel, PmpWeeklySchedule, User
from app.schemas.pmp import PmpDashboardResponse, PmpOrdersResponse
from app.services.audit import log_action
from app.services.pmp import capacity_metrics, dashboard_metrics, import_jose_workbook, import_summary, list_orders, metric_dictionary, reconcile_import, validate_schedule


router = APIRouter(prefix="/pmp", tags=["pmp"])


class PersonnelIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    area: str = Field(min_length=1, max_length=80)
    shift_name: str


class ScheduleIn(BaseModel):
    personnel_id: int
    week_start: date
    available_minutes: float = Field(ge=0)


@router.post("/imports/jose")
def execute_jose_import(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        imported = import_jose_workbook(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_action(db, admin, "pmp_import", "execute", imported.id, after={"valid_rows": imported.valid_rows, "invalid_rows": imported.invalid_rows})
    db.commit()
    return import_summary(db, imported)


@router.get("/imports/latest")
def latest_import(_: User = Depends(current_user), db: Session = Depends(get_db)):
    imported = db.query(PmpImport).order_by(PmpImport.id.desc()).first()
    if not imported:
        return None
    return import_summary(db, imported)


@router.post("/imports/{import_id}/approve")
def approve_import(import_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    imported = db.get(PmpImport, import_id)
    if not imported:
        raise HTTPException(status_code=404, detail="Carga PMP no encontrada")
    reconciliation = reconcile_import(db, imported)
    if not reconciliation["matches"]:
        raise HTTPException(status_code=409, detail="La reconciliación tiene diferencias y no puede aprobarse")
    from datetime import datetime
    imported.approved_at = datetime.utcnow()
    imported.approved_by_user_id = admin.id
    log_action(db, admin, "pmp_import", "approve", imported.id, after={"reconciled": True})
    db.commit()
    return import_summary(db, imported)


@router.get("/areas")
def list_areas(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": area.id, "name": area.name, "is_active": area.is_active} for area in db.query(PmpArea).filter(PmpArea.is_active.is_(True)).order_by(PmpArea.name)]


@router.get("/dashboard", response_model=PmpDashboardResponse)
def pmp_dashboard(
    area: str | None = None,
    status: str | None = Query(default=None, pattern="^(pending|finalized)$"),
    as_of_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    week_start: date | None = None,
    shift: str | None = Query(default=None, pattern="^[123]$"),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        metrics = dashboard_metrics(db, area, status, as_of_date, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # Schedules are weekly records. An as-of date selects its actual Monday
    # rather than pretending the selected day is itself a week_start value.
    capacity_anchor = as_of_date or date_to or date_from
    capacity_week = week_start or (capacity_anchor - timedelta(days=capacity_anchor.weekday()) if capacity_anchor else None)
    capacity = (
        capacity_metrics(db, capacity_week, metrics, area, shift)
        if capacity_week
        else {"week_start": None, "configured": False, "rows": [], "available_shifts": [], "demand_shift_assignment_available": False, "notice": "Seleccione una fecha de corte para consultar la programación semanal."}
    )
    return {
        "metrics": metrics,
        "capacity": capacity,
        "metric_dictionary": metric_dictionary(),
        "filters": {
            "area": area.upper() if area else None,
            "status": status,
            "as_of_date": as_of_date.isoformat() if as_of_date else None,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "week_start": capacity_week.isoformat() if capacity_week else None,
            "shift": shift,
        },
    }


@router.get("/orders", response_model=PmpOrdersResponse)
def pmp_orders(
    area: str | None = None,
    status: str | None = Query(default=None, pattern="^(pending|finalized)$"),
    as_of_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        return list_orders(db, area, status, as_of_date, date_from, date_to, offset, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/personnel")
def list_personnel(area: str | None = None, _: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(PmpPersonnel, PmpArea).join(PmpArea).order_by(PmpPersonnel.name)
    if area:
        query = query.filter(PmpArea.name == area.upper())
    return [{"id": person.id, "name": person.name, "area": pmp_area.name, "shift_name": person.shift_name, "is_active": person.is_active} for person, pmp_area in query.all()]


@router.post("/personnel")
def create_personnel(payload: PersonnelIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        validate_schedule(payload.shift_name, 0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    area = db.query(PmpArea).filter(PmpArea.name == payload.area.strip().upper()).first()
    if not area:
        raise HTTPException(status_code=400, detail="Área PMP no reconocida")
    person = PmpPersonnel(name=payload.name.strip(), pmp_area_id=area.id, shift_name=payload.shift_name)
    db.add(person)
    db.flush()
    log_action(db, admin, "pmp_personnel", "create", person.id, after={"area": area.name, "shift": person.shift_name})
    db.commit()
    return {"id": person.id, "name": person.name, "area": area.name, "shift_name": person.shift_name, "is_active": person.is_active}


@router.post("/schedules")
def set_weekly_schedule(payload: ScheduleIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    person = db.get(PmpPersonnel, payload.personnel_id)
    if not person or not person.is_active:
        raise HTTPException(status_code=400, detail="Personal PMP activo no encontrado")
    try:
        validate_schedule(person.shift_name, payload.available_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    schedule = db.query(PmpWeeklySchedule).filter(PmpWeeklySchedule.pmp_personnel_id == person.id, PmpWeeklySchedule.week_start == payload.week_start).first()
    if not schedule:
        schedule = PmpWeeklySchedule(pmp_personnel_id=person.id, pmp_area_id=person.pmp_area_id, shift_name=person.shift_name, week_start=payload.week_start, available_minutes=payload.available_minutes)
        db.add(schedule)
    else:
        schedule.available_minutes = payload.available_minutes
    db.flush()
    log_action(db, admin, "pmp_schedule", "upsert", schedule.id, after={"week_start": str(schedule.week_start), "available_minutes": schedule.available_minutes})
    db.commit()
    return {"id": schedule.id, "personnel_id": person.id, "week_start": schedule.week_start, "available_minutes": schedule.available_minutes, "shift_name": schedule.shift_name}
