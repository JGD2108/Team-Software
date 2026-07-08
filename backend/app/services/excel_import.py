import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Equipment, MaintenanceEvent, ProductionLine, RawMaintenanceEvent, Shift, UploadedFile, User, ValidationError
from app.services.audit import log_action

REQUIRED_COLUMNS = ["FECHA", "LINEA", "TURNO", "EQUIPO", "DAÑO", "RAZON", "TIEMPO", "FRECUENCIA", "AÑO", "MES"]


def norm(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def norm_key(value) -> str:
    return norm(value).upper()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def event_hash(parts: list) -> str:
    clean = "|".join(norm(p).upper() for p in parts)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def detect_sheets(path: Path) -> list[str]:
    excel = pd.ExcelFile(path)
    matches = []
    for sheet in excel.sheet_names:
        headers = pd.read_excel(path, sheet_name=sheet, nrows=0).columns
        normalized = {norm_key(h) for h in headers}
        if set(REQUIRED_COLUMNS).issubset(normalized):
            matches.append(sheet)
    return matches


def save_upload(upload: UploadFile) -> Path:
    settings = get_settings()
    if not upload.filename or not upload.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx")
    stored = f"{uuid4().hex}_{Path(upload.filename).name}"
    path = settings.upload_dir / stored
    size = 0
    with path.open("wb") as out:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"El archivo supera {settings.max_upload_mb} MB")
            out.write(chunk)
    return path


def _catalogs(db: Session):
    lines = {norm_key(line.name): line for line in db.query(ProductionLine).filter(ProductionLine.is_active.is_(True)).all()}
    equipment = {norm_key(item.name): item for item in db.query(Equipment).filter(Equipment.is_active.is_(True)).all()}
    shifts = {norm_key(item.name): item for item in db.query(Shift).filter(Shift.is_active.is_(True)).all()}
    return lines, equipment, shifts


def _bootstrap_catalogs_from_first_load(db: Session, df: pd.DataFrame) -> None:
    has_confirmed_events = db.query(MaintenanceEvent.id).first() is not None
    if has_confirmed_events:
        return

    lines = {norm_key(line.name): line for line in db.query(ProductionLine).all()}
    for _, row in df.iterrows():
        line_name = norm(row.get("LINEA"))
        if not line_name:
            continue
        key = norm_key(line_name)
        if key not in lines:
            line = ProductionLine(name=line_name, is_active=True)
            db.add(line)
            db.flush()
            lines[key] = line

    equipment = {norm_key(item.name): item for item in db.query(Equipment).all()}
    for _, row in df.iterrows():
        line_name = norm(row.get("LINEA"))
        equipment_name = norm(row.get("EQUIPO"))
        if not line_name or norm_key(equipment_name) in {"", "ERROR"}:
            continue
        line = lines.get(norm_key(line_name))
        key = norm_key(equipment_name)
        if line and key not in equipment:
            item = Equipment(name=equipment_name, production_line_id=line.id, is_active=True)
            db.add(item)
            db.flush()
            equipment[key] = item


def _parse_date(value):
    if value is None or norm(value) == "":
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _parse_float(value):
    try:
        if norm(value) == "":
            return None
        return float(value)
    except ValueError:
        return None


def _parse_month(value) -> int | None:
    months = {
        "ENERO": 1,
        "FEBRERO": 2,
        "MARZO": 3,
        "ABRIL": 4,
        "MAYO": 5,
        "JUNIO": 6,
        "JULIO": 7,
        "AGOSTO": 8,
        "SEPTIEMBRE": 9,
        "SETIEMBRE": 9,
        "OCTUBRE": 10,
        "NOVIEMBRE": 11,
        "DICIEMBRE": 12,
    }
    numeric = _parse_float(value)
    if numeric is not None:
        month = int(numeric)
        return month if 1 <= month <= 12 else None
    key = norm_key(value)
    return months.get(key)


def _add_error(db: Session, upload_id: int, raw_id: int | None, field: str, typ: str, message: str, severity: str):
    db.add(
        ValidationError(
            uploaded_file_id=upload_id,
            raw_event_id=raw_id,
            field_name=field,
            error_type=typ,
            error_message=message,
            severity=severity,
        )
    )


def process_upload(db: Session, upload_file: UploadFile, user: User, selected_sheet: str | None = None) -> UploadedFile:
    path = save_upload(upload_file)
    digest = file_sha256(path)
    sheets = detect_sheets(path)
    if not sheets:
        record = UploadedFile(
            original_filename=upload_file.filename or path.name,
            stored_filename=path.name,
            file_hash=digest,
            uploaded_by_user_id=user.id,
            status="validation_failed",
        )
        db.add(record)
        db.flush()
        _add_error(db, record.id, None, "columns", "missing_required_columns", "No se encontró una hoja con todas las columnas obligatorias", "error")
        log_action(db, user, "uploaded_file", "upload_failed", record.id)
        db.commit()
        return record
    if len(sheets) > 1 and not selected_sheet:
        raise HTTPException(status_code=409, detail={"message": "Varias hojas coinciden. Seleccione una hoja.", "sheets": sheets})
    sheet = selected_sheet or sheets[0]
    if sheet not in sheets:
        raise HTTPException(status_code=400, detail="La hoja seleccionada no contiene las columnas obligatorias")

    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [norm_key(c) for c in df.columns]
    extra_columns = [c for c in df.columns if c not in REQUIRED_COLUMNS]

    record = UploadedFile(
        original_filename=upload_file.filename or path.name,
        stored_filename=path.name,
        file_hash=digest,
        uploaded_by_user_id=user.id,
        status="uploaded",
        total_rows=len(df),
    )
    db.add(record)
    db.flush()

    if extra_columns:
        _add_error(db, record.id, None, "columns", "extra_columns", f"Columnas extra ignoradas: {', '.join(extra_columns)}", "warning")

    _bootstrap_catalogs_from_first_load(db, df)
    lines, equipment, shifts = _catalogs(db)
    existing_hashes = {x[0] for x in db.query(MaintenanceEvent.event_hash).all()}
    valid_rows = error_rows = warning_rows = 0

    for index, row in df.iterrows():
        payload = {col: norm(row.get(col)) for col in REQUIRED_COLUMNS}
        row_errors = []
        row_warnings = []
        event_date = _parse_date(payload["FECHA"])
        downtime = _parse_float(payload["TIEMPO"])
        frequency = _parse_float(payload["FRECUENCIA"])
        line = lines.get(norm_key(payload["LINEA"]))
        equip = equipment.get(norm_key(payload["EQUIPO"]))

        if not event_date:
            row_errors.append(("FECHA", "invalid_date", "FECHA es obligatoria y debe ser fecha"))
        if not payload["LINEA"]:
            row_errors.append(("LINEA", "required", "LINEA es obligatoria"))
        elif not line:
            row_errors.append(("LINEA", "unknown_line", "Línea no reconocida; requiere aprobación/corrección admin"))
        if norm_key(payload["EQUIPO"]) in {"", "ERROR"}:
            row_errors.append(("EQUIPO", "pending_equipment", "Equipo vacío o marcado como error; requiere corrección"))
        elif not equip:
            row_errors.append(("EQUIPO", "unknown_equipment", "Equipo no reconocido; requiere aprobación/corrección admin"))
        if not payload["DAÑO"]:
            row_errors.append(("DAÑO", "required", "DAÑO es obligatorio"))
        if not payload["RAZON"]:
            row_errors.append(("RAZON", "required", "RAZON es obligatorio"))
        if downtime is None or downtime < 0:
            row_errors.append(("TIEMPO", "invalid_number", "TIEMPO debe ser numérico y mayor o igual a 0"))
        if frequency is None or frequency < 1:
            row_errors.append(("FRECUENCIA", "invalid_number", "FRECUENCIA debe ser numérica y mayor o igual a 1"))
        if event_date:
            if payload["AÑO"] and str(event_date.year) != str(int(float(payload["AÑO"])) if _parse_float(payload["AÑO"]) else payload["AÑO"]):
                row_warnings.append(("AÑO", "year_mismatch", "AÑO no coincide con FECHA"))
            parsed_month = _parse_month(payload["MES"])
            if payload["MES"] and parsed_month != event_date.month:
                row_warnings.append(("MES", "month_mismatch", "MES no coincide con FECHA"))
        if line and equip and equip.production_line_id != line.id:
            row_warnings.append(("EQUIPO", "line_mismatch", "El equipo pertenece a otra línea maestra"))
        if not payload["TURNO"]:
            row_warnings.append(("TURNO", "empty_shift", "Turno vacío; se tratará como Sin turno"))
        h = event_hash([payload["FECHA"], payload["LINEA"], payload["TURNO"], payload["EQUIPO"], payload["DAÑO"], payload["RAZON"], payload["TIEMPO"], payload["FRECUENCIA"]])
        if h in existing_hashes:
            row_warnings.append(("event_hash", "potential_duplicate", "Posible duplicado contra datos ya confirmados"))

        status = "valid"
        if row_errors:
            status = "pending_correction"
            error_rows += 1
        elif row_warnings:
            status = "warning"
            warning_rows += 1
        else:
            valid_rows += 1

        raw = RawMaintenanceEvent(
            uploaded_file_id=record.id,
            row_number=int(index) + 2,
            raw_fecha=payload["FECHA"],
            raw_linea=payload["LINEA"],
            raw_turno=payload["TURNO"],
            raw_equipo=payload["EQUIPO"],
            raw_dano=payload["DAÑO"],
            raw_razon=payload["RAZON"],
            raw_tiempo=payload["TIEMPO"],
            raw_frecuencia=payload["FRECUENCIA"],
            raw_anio=payload["AÑO"],
            raw_mes=payload["MES"],
            raw_payload_json=json.dumps(payload, ensure_ascii=False),
            validation_status=status,
            validation_errors_json=json.dumps(row_errors + row_warnings, ensure_ascii=False),
        )
        db.add(raw)
        db.flush()
        for field, typ, msg in row_errors:
            _add_error(db, record.id, raw.id, field, typ, msg, "error")
        for field, typ, msg in row_warnings:
            _add_error(db, record.id, raw.id, field, typ, msg, "warning")

    record.valid_rows = valid_rows
    record.error_rows = error_rows
    record.warning_rows = warning_rows + (1 if extra_columns else 0)
    record.status = "pending_corrections" if error_rows else "ready_to_confirm"
    log_action(db, user, "uploaded_file", "upload", record.id, after={"rows": len(df), "status": record.status})
    db.commit()
    db.refresh(record)
    return record


def apply_correction(
    db: Session,
    raw: RawMaintenanceEvent,
    user: User,
    production_line_id: int | None = None,
    equipment_id: int | None = None,
    shift_name: str | None = None,
    damage_description: str | None = None,
    reason_description: str | None = None,
    downtime_minutes: float | None = None,
    frequency: float | None = None,
    event_date=None,
):
    before = {
        "fecha": raw.raw_fecha,
        "linea": raw.raw_linea,
        "turno": raw.raw_turno,
        "equipo": raw.raw_equipo,
        "dano": raw.raw_dano,
        "razon": raw.raw_razon,
        "tiempo": raw.raw_tiempo,
        "frecuencia": raw.raw_frecuencia,
    }
    if production_line_id:
        line = db.get(ProductionLine, production_line_id)
        if not line or not line.is_active:
            raise HTTPException(status_code=400, detail="Línea inválida")
        raw.raw_linea = line.name
    if equipment_id:
        equip = db.get(Equipment, equipment_id)
        if not equip or not equip.is_active:
            raise HTTPException(status_code=400, detail="Equipo inválido")
        raw.raw_equipo = equip.name
        if not production_line_id:
            raw.raw_linea = equip.production_line.name
    if shift_name is not None:
        raw.raw_turno = shift_name.strip() or None
    if damage_description is not None:
        raw.raw_dano = damage_description.strip()
    if reason_description is not None:
        raw.raw_razon = reason_description.strip()
    if downtime_minutes is not None:
        if downtime_minutes < 0:
            raise HTTPException(status_code=400, detail="TIEMPO debe ser mayor o igual a 0")
        raw.raw_tiempo = str(downtime_minutes)
    if frequency is not None:
        if frequency < 1:
            raise HTTPException(status_code=400, detail="FRECUENCIA debe ser mayor o igual a 1")
        raw.raw_frecuencia = str(frequency)
    if event_date is not None:
        raw.raw_fecha = event_date.isoformat()
        raw.raw_anio = str(event_date.year)
        raw.raw_mes = str(event_date.month)
    db.query(ValidationError).filter(ValidationError.raw_event_id == raw.id, ValidationError.severity == "error").update(
        {"status": "resolved", "resolved_by_user_id": user.id, "resolved_at": datetime.utcnow()}
    )
    raw.validation_status = "warning"
    raw.validation_errors_json = "[]"
    log_action(
        db,
        user,
        "raw_maintenance_event",
        "correct",
        raw.id,
        before=before,
        after={
            "fecha": raw.raw_fecha,
            "linea": raw.raw_linea,
            "turno": raw.raw_turno,
            "equipo": raw.raw_equipo,
            "dano": raw.raw_dano,
            "razon": raw.raw_razon,
            "tiempo": raw.raw_tiempo,
            "frecuencia": raw.raw_frecuencia,
        },
    )

def confirm_upload(db: Session, upload: UploadedFile, user: User):
    open_errors = db.query(ValidationError).filter(
        ValidationError.uploaded_file_id == upload.id,
        ValidationError.severity == "error",
        ValidationError.status == "open",
    ).count()
    if open_errors:
        raise HTTPException(status_code=409, detail="La carga aún tiene errores bloqueantes")
    lines, equipment, shifts = _catalogs(db)
    raws = db.query(RawMaintenanceEvent).filter(RawMaintenanceEvent.uploaded_file_id == upload.id).all()
    created = 0
    for raw in raws:
        event_date = _parse_date(raw.raw_fecha)
        line = lines.get(norm_key(raw.raw_linea))
        equip = equipment.get(norm_key(raw.raw_equipo))
        if not event_date or not line or not equip:
            raise HTTPException(status_code=409, detail=f"Fila {raw.row_number} no está lista para confirmar")
        shift = shifts.get(norm_key(raw.raw_turno or "Sin turno"))
        if not shift:
            shift = Shift(name=raw.raw_turno or "Sin turno", is_active=True)
            db.add(shift)
            db.flush()
            shifts[norm_key(shift.name)] = shift
        downtime = _parse_float(raw.raw_tiempo) or 0
        frequency = _parse_float(raw.raw_frecuencia) or 1
        h = event_hash([raw.raw_fecha, raw.raw_linea, raw.raw_turno, raw.raw_equipo, raw.raw_dano, raw.raw_razon, raw.raw_tiempo, raw.raw_frecuencia])
        db.add(
            MaintenanceEvent(
                uploaded_file_id=upload.id,
                event_hash=h,
                event_date=event_date,
                production_line_id=line.id,
                shift_id=shift.id,
                equipment_id=equip.id,
                damage_description=raw.raw_dano or "",
                reason_description=raw.raw_razon or "",
                downtime_minutes=downtime,
                frequency=frequency,
                year=event_date.year,
                month=event_date.month,
                corrected_from_raw_event_id=raw.id,
            )
        )
        created += 1
    upload.status = "confirmed"
    upload.valid_rows = len(raws)
    upload.error_rows = 0
    upload.confirmed_at = datetime.utcnow()
    upload.confirmed_by_user_id = user.id
    log_action(db, user, "uploaded_file", "confirm", upload.id, after={"events": created})

