from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.models import RawMaintenanceEvent, UploadedFile, User, ValidationError
from app.schemas.common import CorrectionIn, UploadOut
from app.services.audit import log_action
from app.services.excel_import import apply_correction, confirm_upload, process_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])
corrections_router = APIRouter(tags=["corrections"])


@router.post("", response_model=UploadOut)
def upload_excel(
    file: UploadFile = File(...),
    sheet_name: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return process_upload(db, file, user, selected_sheet=sheet_name)


@router.get("", response_model=list[UploadOut])
def list_uploads(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(UploadedFile).order_by(UploadedFile.uploaded_at.desc()).all()


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(upload_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    upload = db.get(UploadedFile, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    return upload


@router.get("/{upload_id}/preview")
def preview_upload(upload_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(RawMaintenanceEvent).filter(RawMaintenanceEvent.uploaded_file_id == upload_id).order_by(RawMaintenanceEvent.row_number).limit(200).all()
    return [
        {
            "id": r.id,
            "row_number": r.row_number,
            "fecha": r.raw_fecha,
            "linea": r.raw_linea,
            "turno": r.raw_turno or "Sin turno",
            "equipo": r.raw_equipo,
            "dano": r.raw_dano,
            "razon": r.raw_razon,
            "tiempo": r.raw_tiempo,
            "frecuencia": r.raw_frecuencia,
            "status": r.validation_status,
            "errors": r.validation_errors_json,
        }
        for r in rows
    ]


@router.get("/{upload_id}/errors")
def upload_errors(upload_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    errors = db.query(ValidationError).filter(ValidationError.uploaded_file_id == upload_id).order_by(ValidationError.severity, ValidationError.created_at).all()
    return [
        {
            "id": e.id,
            "raw_event_id": e.raw_event_id,
            "field_name": e.field_name,
            "error_type": e.error_type,
            "error_message": e.error_message,
            "severity": e.severity,
            "status": e.status,
        }
        for e in errors
    ]


@router.post("/{upload_id}/confirm", response_model=UploadOut)
def confirm(upload_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    upload = db.get(UploadedFile, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    if upload.status == "confirmed":
        return upload
    confirm_upload(db, upload, user)
    db.commit()
    db.refresh(upload)
    return upload


@router.post("/{upload_id}/reject", response_model=UploadOut)
def reject(upload_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    upload = db.get(UploadedFile, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    upload.status = "rejected"
    log_action(db, admin, "uploaded_file", "reject", upload.id)
    db.commit()
    db.refresh(upload)
    return upload


@corrections_router.get("/corrections/pending")
def pending_corrections(_: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(RawMaintenanceEvent)
        .join(UploadedFile, UploadedFile.id == RawMaintenanceEvent.uploaded_file_id)
        .filter(
            RawMaintenanceEvent.validation_status == "pending_correction",
            UploadedFile.status == "pending_corrections",
        )
        .order_by(RawMaintenanceEvent.created_at.desc())
        .limit(300)
        .all()
    )
    return [
        {
            "id": r.id,
            "uploaded_file_id": r.uploaded_file_id,
            "row_number": r.row_number,
            "fecha": r.raw_fecha,
            "linea": r.raw_linea,
            "equipo": r.raw_equipo,
            "turno": r.raw_turno or "Sin turno",
            "dano": r.raw_dano,
            "razon": r.raw_razon,
            "errors": r.validation_errors_json,
        }
        for r in rows
    ]


@corrections_router.patch("/raw-events/{raw_event_id}/correction")
def correct_raw_event(raw_event_id: int, payload: CorrectionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    raw = db.get(RawMaintenanceEvent, raw_event_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Registro raw no encontrado")
    apply_correction(db, raw, user, payload.production_line_id, payload.equipment_id, payload.shift_name)
    upload = db.get(UploadedFile, raw.uploaded_file_id)
    if upload:
        open_errors = db.query(ValidationError).filter(ValidationError.uploaded_file_id == upload.id, ValidationError.severity == "error", ValidationError.status == "open").count()
        upload.error_rows = open_errors
        upload.status = "ready_to_confirm" if open_errors == 0 else "pending_corrections"
    db.commit()
    return {"ok": True}
