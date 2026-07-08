import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models import ReportExport, User
from app.schemas.common import ReportRequest
from app.services.audit import log_action
from app.services.report_pdf import build_management_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/management-pdf")
def generate_management_pdf(payload: ReportRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    filename = f"reporte_gerencial_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    path = get_settings().report_dir / filename
    build_management_pdf(db, path, payload)
    report = ReportExport(
        generated_by_user_id=admin.id,
        report_type="management",
        date_from=payload.date_from,
        date_to=payload.date_to,
        filters_json=json.dumps(payload.model_dump(), default=str),
        file_path=str(path),
    )
    db.add(report)
    db.flush()
    log_action(db, admin, "report_export", "generate", report.id, after={"file": filename})
    db.commit()
    return {"id": report.id, "filename": filename}


@router.get("")
def list_reports(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    reports = db.query(ReportExport).order_by(ReportExport.created_at.desc()).all()
    return [{"id": r.id, "report_type": r.report_type, "created_at": r.created_at, "file_path": Path(r.file_path).name} for r in reports]


@router.get("/{report_id}/download")
def download_report(report_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    report = db.get(ReportExport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return FileResponse(report.file_path, media_type="application/pdf", filename=Path(report.file_path).name)
