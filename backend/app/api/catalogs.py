from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.models import Equipment, FailureMode, MaintenanceEvent, ProductionLine, Shift, User
from app.schemas.common import EquipmentIn, EquipmentOut, FailureModeIn, FailureModeOut, LineIn, LineOut
from app.services.audit import log_action
from app.services.normalization import normalize_report_text

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
        term = f"%{search.strip()}%"
        query = query.filter(or_(ProductionLine.name.ilike(term), ProductionLine.code.ilike(term)))
    return query.order_by(ProductionLine.code.nullslast(), ProductionLine.name).all()


@router.post("/production-lines", response_model=LineOut)
def create_line(payload: LineIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.name.strip()
    code = payload.code.strip().upper() if payload.code else None
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if db.query(ProductionLine).filter(func.lower(ProductionLine.name) == name.lower()).first():
        raise HTTPException(status_code=409, detail="El área ya existe")
    if code and db.query(ProductionLine).filter(ProductionLine.code == code).first():
        raise HTTPException(status_code=409, detail="El código del área ya existe")
    line = ProductionLine(name=name, code=code, is_active=payload.is_active)
    db.add(line)
    db.flush()
    log_action(db, admin, "production_line", "create", line.id, after={"name": line.name, "code": line.code})
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}", response_model=LineOut)
def update_line(line_id: int, payload: LineIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    name = payload.name.strip()
    duplicate = db.query(ProductionLine).filter(func.lower(ProductionLine.name) == name.lower(), ProductionLine.id != line_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="El área ya existe")
    before = {"name": line.name, "code": line.code, "is_active": line.is_active}
    line.name = name
    if payload.code:
        line.code = payload.code.strip().upper()
    line.is_active = payload.is_active
    log_action(db, admin, "production_line", "update", line.id, before=before, after={"name": line.name, "code": line.code, "is_active": line.is_active})
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}/activate", response_model=LineOut)
def activate_line(line_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    line.is_active = True
    log_action(db, admin, "production_line", "activate", line.id)
    db.commit()
    db.refresh(line)
    return line


@router.patch("/production-lines/{line_id}/deactivate", response_model=LineOut)
def deactivate_line(line_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    line = db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Área no encontrada")
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
    area_code: str | None = None,
    process_code: str | None = None,
    hierarchy_level: int | None = None,
    criticality: str | None = None,
    specialty: str | None = None,
    reportable: bool | None = None,
    active: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Equipment)
    if not include_inactive:
        query = query.filter(Equipment.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            Equipment.code.ilike(term),
            Equipment.name.ilike(term),
            Equipment.brand.ilike(term),
            Equipment.model.ilike(term),
            Equipment.serial_number.ilike(term),
            Equipment.location.ilike(term),
            Equipment.qr_code.ilike(term),
        ))
    if production_line_id:
        query = query.filter(Equipment.production_line_id == production_line_id)
    if area_code:
        query = query.filter(Equipment.area_code == area_code)
    if process_code:
        query = query.filter(Equipment.process_code == process_code)
    if hierarchy_level:
        query = query.filter(Equipment.hierarchy_level == hierarchy_level)
    if criticality:
        query = query.filter(Equipment.criticality == criticality)
    if specialty:
        query = query.filter(Equipment.specialty == specialty)
    if reportable is not None:
        query = query.filter(Equipment.is_reportable.is_(reportable))
    if active is not None:
        query = query.filter(Equipment.is_active.is_(active))
    return query.order_by(Equipment.code.nullslast(), Equipment.name).offset(offset).limit(limit).all()


@router.get("/equipment/filter-options")
def equipment_filter_options(_: User = Depends(current_user), db: Session = Depends(get_db)):
    catalog = db.query(Equipment).filter(Equipment.code.is_not(None))
    plants = db.query(Equipment.plant_code, Equipment.plant_name).filter(Equipment.hierarchy_level == 1).order_by(Equipment.plant_code).all()
    areas = db.query(Equipment.area_code, Equipment.area_name).filter(Equipment.hierarchy_level == 2).order_by(Equipment.area_code).all()
    processes = db.query(Equipment.process_code, Equipment.process_name, Equipment.area_code).filter(Equipment.hierarchy_level == 3).order_by(Equipment.process_code).all()
    criticalities = [row[0] for row in db.query(Equipment.criticality).filter(Equipment.criticality.is_not(None)).distinct().order_by(Equipment.criticality).all()]
    specialties = [row[0] for row in db.query(Equipment.specialty).filter(Equipment.specialty.is_not(None)).distinct().order_by(Equipment.specialty).all()]
    return {
        "total": catalog.count(),
        "active": catalog.filter(Equipment.is_active.is_(True)).count(),
        "reportable": catalog.filter(Equipment.is_reportable.is_(True)).count(),
        "plants": [{"code": code, "name": name} for code, name in plants],
        "areas": [{"code": code, "name": name} for code, name in areas],
        "processes": [{"code": code, "name": name, "area_code": parent} for code, name, parent in processes],
        "criticalities": criticalities,
        "specialties": specialties,
        "levels": [
            {"id": 1, "name": "Planta"},
            {"id": 2, "name": "Área"},
            {"id": 3, "name": "Proceso / Línea"},
            {"id": 4, "name": "Equipo"},
            {"id": 5, "name": "Sub-equipo / Componente"},
        ],
    }


def taxonomy_for(code: str, line: ProductionLine, db: Session):
    normalized = code.strip().upper().replace(" ", "")
    if not normalized or "-" not in normalized:
        raise HTTPException(status_code=400, detail="Usa un código taxonómico, por ejemplo BA-EM-E1-BT18")
    if line.code and not normalized.startswith(f"{line.code}-"):
        raise HTTPException(status_code=400, detail=f"El código debe comenzar por {line.code}-")
    segments = normalized.split("-")
    process_code = "-".join(segments[:3]) if len(segments) >= 3 else None
    process = db.query(Equipment).filter(Equipment.code == process_code).first() if process_code else None
    return {
        "code": normalized,
        "parent_code": "-".join(segments[:-1]),
        "hierarchy_level": len(segments),
        "plant_code": segments[0],
        "plant_name": "PLANTA BARRANQUILLA" if segments[0] == "BA" else segments[0],
        "area_code": line.code,
        "area_name": line.name,
        "process_code": process_code,
        "process_name": process.name if process else None,
        "is_reportable": True,
    }


@router.post("/equipment", response_model=EquipmentOut)
def create_equipment(payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = payload.name.strip()
    line = db.get(ProductionLine, payload.production_line_id)
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not line:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    if not payload.code:
        raise HTTPException(status_code=400, detail="El código taxonómico es obligatorio")
    code = payload.code.strip().upper().replace(" ", "")
    if db.query(Equipment).filter(Equipment.code == code).first():
        raise HTTPException(status_code=409, detail="El código del equipo ya existe")
    equipment = Equipment(
        name=name,
        production_line_id=payload.production_line_id,
        is_active=payload.is_active,
        source_status="Habilitado." if payload.is_active else "Inhabilitado",
        **taxonomy_for(code, line, db),
    )
    db.add(equipment)
    db.flush()
    log_action(db, admin, "equipment", "create", equipment.id, after={"name": equipment.name, "code": equipment.code})
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}", response_model=EquipmentOut)
def update_equipment(equipment_id: int, payload: EquipmentIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    line = db.get(ProductionLine, payload.production_line_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    if not line:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    before = {"name": equipment.name, "code": equipment.code, "is_active": equipment.is_active}
    equipment.name = payload.name.strip()
    equipment.production_line_id = payload.production_line_id
    equipment.is_active = payload.is_active
    equipment.source_status = "Habilitado." if payload.is_active else "Inhabilitado"
    if payload.code and payload.code.strip().upper().replace(" ", "") != equipment.code:
        next_code = payload.code.strip().upper().replace(" ", "")
        if db.query(Equipment).filter(Equipment.code == next_code, Equipment.id != equipment_id).first():
            raise HTTPException(status_code=409, detail="El código del equipo ya existe")
        for field, value in taxonomy_for(next_code, line, db).items():
            setattr(equipment, field, value)
    log_action(db, admin, "equipment", "update", equipment.id, before=before, after={"name": equipment.name, "code": equipment.code, "is_active": equipment.is_active})
    db.commit()
    db.refresh(equipment)
    return equipment


@router.patch("/equipment/{equipment_id}/activate", response_model=EquipmentOut)
def activate_equipment(equipment_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    equipment.is_active = True
    equipment.source_status = "Habilitado."
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
    equipment.source_status = "Inhabilitado"
    log_action(db, admin, "equipment", "deactivate", equipment.id)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("/shifts")
def list_shifts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": shift.id, "name": shift.name, "is_active": shift.is_active} for shift in db.query(Shift).filter(Shift.is_active.is_(True)).order_by(Shift.name).all()]


@router.get("/failure-modes", response_model=list[FailureModeOut])
def list_failure_modes(
    include_inactive: bool = True,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = db.query(FailureMode)
    if not include_inactive:
        query = query.filter(FailureMode.is_active.is_(True))
    return query.order_by(FailureMode.name).all()


@router.post("/failure-modes", response_model=FailureModeOut)
def create_failure_mode(payload: FailureModeIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    name = normalize_report_text(payload.name)
    if db.query(FailureMode).filter(func.lower(FailureMode.name) == name.lower()).first():
        raise HTTPException(status_code=409, detail="El modo de falla ya existe")
    mode = FailureMode(name=name, is_active=payload.is_active)
    db.add(mode)
    db.flush()
    log_action(db, admin, "failure_mode", "create", mode.id, after={"name": mode.name})
    db.commit()
    db.refresh(mode)
    return mode


@router.patch("/failure-modes/{mode_id}/{action}", response_model=FailureModeOut)
def toggle_failure_mode(mode_id: int, action: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if action not in {"activate", "deactivate"}:
        raise HTTPException(status_code=400, detail="Acción inválida")
    mode = db.get(FailureMode, mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Modo de falla no encontrado")
    mode.is_active = action == "activate"
    log_action(db, admin, "failure_mode", action, mode.id)
    db.commit()
    db.refresh(mode)
    return mode


@router.get("/catalog-stats")
def catalog_stats(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return {
        "lines": db.query(ProductionLine).count(),
        "active_lines": db.query(ProductionLine).filter(ProductionLine.is_active.is_(True)).count(),
        "equipment": db.query(Equipment).count(),
        "active_equipment": db.query(Equipment).filter(Equipment.is_active.is_(True)).count(),
        "reportable_equipment": db.query(Equipment).filter(Equipment.is_reportable.is_(True)).count(),
        "placeholder_equipment": db.query(Equipment).filter(Equipment.name.ilike("Equipo sin identificar%")).count(),
        "validated_events": db.query(MaintenanceEvent).count(),
    }
