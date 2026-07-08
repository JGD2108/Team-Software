from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.models import Equipment, MaintenanceEvent, ProductionLine, Shift, User
from app.schemas.common import EquipmentIn, EquipmentOut, LineIn, LineOut
from app.services.audit import log_action

router = APIRouter(tags=["catalogs"])


@router.get("/production-lines", response_model=list[LineOut])
def list_lines(
    include_inactive: bool = True,
    search: str | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ProductionLine)
    if not include_inactive:
        query = query.filter(ProductionLine.is_active.is_(True))
    if search:
        query = query.filter(func.lower(ProductionLine.name).contains(search.lower()))
    return query.order_by(ProductionLine.name).all()


@router.post("/production-lines", response_model=LineOut)
def create_line(payload: LineIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if db.query(ProductionLine).filter(func.lower(ProductionLine.name) == name.lower()).first():
        raise HTTPException(status_code=409, detail="La línea ya existe")
    line = ProductionLine(name=name, is_active=payload.is_active)
    db.add(line)
    db.flush()
    log_action(db, admin, "production_line", "create", line.id, after={"name": line.name})
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}", response_model=LineOut)
def update_line(line_id: int, payload: LineIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    name = payload.name.strip()
    duplicate = db.query(ProductionLine).filter(func.lower(ProductionLine.name) == name.lower(), ProductionLine.id != line_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="La línea ya existe")
    before = {"name": line.name, "is_active": line.is_active}
    line.name = name
    line.is_active = payload.is_active
    log_action(db, admin, "production_line", "update", line.id, before=before, after={"name": line.name, "is_active": line.is_active})
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}/activate", response_model=LineOut)
def activate_line(line_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    line.is_active = True
    log_action(db, admin, "production_line", "activate", line.id)
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}/deactivate", response_model=LineOut)
def deactivate_line(line_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    line.is_active = False
    log_action(db, admin, "production_line", "deactivate", line.id)
    db.commit()
    db.refresh(line)
    return line


@router.get("/equipment", response_model=list[EquipmentOut])
def list_equipment(
    include_inactive: bool = True,
    search: str | None = None,
    production_line_id: int | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Equipment)
    if not include_inactive:
        query = query.filter(Equipment.is_active.is_(True))
    if search:
        query = query.filter(func.lower(Equipment.name).contains(search.lower()))
    if production_line_id:
        query = query.filter(Equipment.production_line_id == production_line_id)
    return query.order_by(Equipment.name).all()


@router.post("/equipment", response_model=EquipmentOut)
def create_equipment(payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not db.get(ProductionLine, payload.production_line_id):
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    if db.query(Equipment).filter(func.lower(Equipment.name) == name.lower(), Equipment.production_line_id == payload.production_line_id).first():
        raise HTTPException(status_code=409, detail="El equipo ya existe en esa línea")
    equipment = Equipment(name=name, production_line_id=payload.production_line_id, is_active=payload.is_active)
    db.add(equipment)
    db.flush()
    log_action(db, admin, "equipment", "create", equipment.id, after={"name": equipment.name, "production_line_id": equipment.production_line_id})
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}", response_model=EquipmentOut)
def update_equipment(equipment_id: int, payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    name = payload.name.strip()
    if not db.get(ProductionLine, payload.production_line_id):
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    duplicate = db.query(Equipment).filter(
        func.lower(Equipment.name) == name.lower(),
        Equipment.production_line_id == payload.production_line_id,
        Equipment.id != equipment_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="El equipo ya existe en esa línea")
    before = {"name": equipment.name, "production_line_id": equipment.production_line_id, "is_active": equipment.is_active}
    equipment.name = name
    equipment.production_line_id = payload.production_line_id
    equipment.is_active = payload.is_active
    log_action(db, admin, "equipment", "update", equipment.id, before=before, after={"name": equipment.name, "production_line_id": equipment.production_line_id, "is_active": equipment.is_active})
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}/activate", response_model=EquipmentOut)
def activate_equipment(equipment_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipment.is_active = True
    log_action(db, admin, "equipment", "activate", equipment.id)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}/deactivate", response_model=EquipmentOut)
def deactivate_equipment(equipment_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipment.is_active = False
    log_action(db, admin, "equipment", "deactivate", equipment.id)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("/shifts")
def list_shifts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": shift.id, "name": shift.name, "is_active": shift.is_active} for shift in db.query(Shift).order_by(Shift.name).all()]


@router.get("/catalog-stats")
def catalog_stats(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return {
        "lines": db.query(ProductionLine).count(),
        "active_lines": db.query(ProductionLine).filter(ProductionLine.is_active.is_(True)).count(),
        "equipment": db.query(Equipment).count(),
        "active_equipment": db.query(Equipment).filter(Equipment.is_active.is_(True)).count(),
        "placeholder_equipment": db.query(Equipment).filter(Equipment.name.ilike("Equipo sin identificar%")).count(),
        "validated_events": db.query(MaintenanceEvent).count(),
    }
