from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.models import Equipment, ProductionLine, User
from app.schemas.common import EquipmentIn, EquipmentOut, LineIn, LineOut
from app.services.audit import log_action

router = APIRouter(tags=["catalogs"])


@router.get("/production-lines", response_model=list[LineOut])
def list_lines(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(ProductionLine).order_by(ProductionLine.name).all()


@router.post("/production-lines", response_model=LineOut)
def create_line(payload: LineIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = ProductionLine(name=payload.name.strip(), is_active=payload.is_active)
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
    before = {"name": line.name, "is_active": line.is_active}
    line.name = payload.name.strip()
    line.is_active = payload.is_active
    log_action(db, admin, "production_line", "update", line.id, before=before, after={"name": line.name, "is_active": line.is_active})
    db.commit()
    db.refresh(line)
    return line


@router.get("/equipment", response_model=list[EquipmentOut])
def list_equipment(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Equipment).order_by(Equipment.name).all()


@router.post("/equipment", response_model=EquipmentOut)
def create_equipment(payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(ProductionLine, payload.production_line_id):
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    equipment = Equipment(name=payload.name.strip(), production_line_id=payload.production_line_id, is_active=payload.is_active)
    db.add(equipment)
    db.flush()
    log_action(db, admin, "equipment", "create", equipment.id, after={"name": equipment.name})
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}", response_model=EquipmentOut)
def update_equipment(equipment_id: int, payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    before = {"name": equipment.name, "line": equipment.production_line_id, "active": equipment.is_active}
    equipment.name = payload.name.strip()
    equipment.production_line_id = payload.production_line_id
    equipment.is_active = payload.is_active
    log_action(db, admin, "equipment", "update", equipment.id, before=before, after={"name": equipment.name})
    db.commit()
    db.refresh(equipment)
    return equipment
