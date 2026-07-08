from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Equipment, MaintenanceEvent, ProductionLine, ValidationError
from app.schemas.common import ReportRequest


def _base_query(db: Session, filters: ReportRequest):
    q = db.query(MaintenanceEvent)
    if filters.date_from:
        q = q.filter(MaintenanceEvent.event_date >= filters.date_from)
    if filters.date_to:
        q = q.filter(MaintenanceEvent.event_date <= filters.date_to)
    if filters.production_line_id:
        q = q.filter(MaintenanceEvent.production_line_id == filters.production_line_id)
    if filters.equipment_id:
        q = q.filter(MaintenanceEvent.equipment_id == filters.equipment_id)
    if filters.shift_id:
        q = q.filter(MaintenanceEvent.shift_id == filters.shift_id)
    return q


def build_management_pdf(db: Session, path: Path, filters: ReportRequest) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=letter, title="Reporte gerencial de mantenimiento")
    story = []
    q = _base_query(db, filters)
    total_minutes = q.with_entities(func.coalesce(func.sum(MaintenanceEvent.downtime_minutes), 0)).scalar() or 0
    total_events = q.count()
    total_frequency = q.with_entities(func.coalesce(func.sum(MaintenanceEvent.frequency), 0)).scalar() or 0
    equipment_rows = (
        q.join(Equipment)
        .with_entities(Equipment.name, func.sum(MaintenanceEvent.downtime_minutes).label("minutes"), func.sum(MaintenanceEvent.frequency).label("frequency"))
        .group_by(Equipment.name)
        .order_by(func.sum(MaintenanceEvent.downtime_minutes).desc())
        .limit(15)
        .all()
    )
    line_rows = (
        q.join(ProductionLine)
        .with_entities(ProductionLine.name, func.sum(MaintenanceEvent.downtime_minutes).label("minutes"))
        .group_by(ProductionLine.name)
        .order_by(func.sum(MaintenanceEvent.downtime_minutes).desc())
        .all()
    )
    critical_equipment = equipment_rows[0].name if equipment_rows else "Sin datos"
    critical_line = line_rows[0].name if line_rows else "Sin datos"

    story.append(Paragraph("Reporte gerencial de mantenimiento", styles["Title"]))
    story.append(Paragraph(f"Periodo: {filters.date_from or 'inicio'} a {filters.date_to or 'fin'}", styles["Normal"]))
    story.append(Paragraph("Generado automaticamente por el MVP interno.", styles["Normal"]))
    story.append(PageBreak())

    story.append(Paragraph("Resumen ejecutivo", styles["Heading1"]))
    summary = [
        ["Tiempo total perdido", f"{total_minutes:.0f} min / {total_minutes / 60:.2f} h"],
        ["Total de fallas/paradas", str(total_events)],
        ["Frecuencia total", f"{total_frequency:.0f}"],
        ["Equipo mas critico", critical_equipment],
        ["Linea mas critica", critical_line],
    ]
    story.append(Table(summary, colWidths=[220, 260], style=_table_style()))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Observacion principal: priorizar los equipos con mayor tiempo perdido y revisar causas repetitivas.", styles["Normal"]))
    story.append(PageBreak())

    story.append(Paragraph("Pareto de equipos", styles["Heading1"]))
    table = [["Equipo", "Tiempo perdido", "Frecuencia", "% acumulado"]]
    running = 0
    for row in equipment_rows:
        running += row.minutes or 0
        pct = (running / total_minutes * 100) if total_minutes else 0
        table.append([row.name, f"{row.minutes or 0:.0f}", f"{row.frequency or 0:.0f}", f"{pct:.1f}%"])
    story.append(Table(table, repeatRows=1, style=_table_style()))
    story.append(PageBreak())

    story.append(Paragraph("Analisis por linea", styles["Heading1"]))
    line_table = [["Linea", "Tiempo perdido", "Participacion"]]
    for row in line_rows:
        pct = ((row.minutes or 0) / total_minutes * 100) if total_minutes else 0
        line_table.append([row.name, f"{row.minutes or 0:.0f}", f"{pct:.1f}%"])
    story.append(Table(line_table, repeatRows=1, style=_table_style()))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Calidad del dato", styles["Heading1"]))
    open_errors = db.query(ValidationError).filter(ValidationError.severity == "error", ValidationError.status == "open").count()
    corrected = db.query(ValidationError).filter(ValidationError.status == "resolved").count()
    story.append(Table([["Errores abiertos", open_errors], ["Registros corregidos", corrected]], style=_table_style()))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Recomendaciones", styles["Heading1"]))
    for text in [
        "Priorizar revision de equipos con mayor tiempo perdido.",
        "Revisar equipos con alta frecuencia.",
        "Estandarizar captura de DANO y RAZON.",
        "Disminuir el uso de 'error' como equipo.",
        "Mejorar captura de turno.",
    ]:
        story.append(Paragraph(f"- {text}", styles["Normal"]))
    doc.build(story)


def _table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a3d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4c1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]
    )
