from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="plant_user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductionLine(Base, TimestampMixin):
    __tablename__ = "production_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    code: Mapped[str | None] = mapped_column(String(40), unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="production_line")


class Equipment(Base, TimestampMixin):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    production_line_id: Mapped[int | None] = mapped_column(ForeignKey("production_lines.id"), index=True, nullable=True)
    code: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    parent_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hierarchy_level: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    plant_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plant_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    area_code: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    area_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    process_code: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    process_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_reportable: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    qr_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    criticality: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(30), index=True, nullable=True)
    grouping: Mapped[str | None] = mapped_column(String(80), nullable=True)
    analysis_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    pdt_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    financial_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    production_line: Mapped[ProductionLine | None] = relationship(back_populates="equipment")


class Shift(Base, TimestampMixin):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class FailureMode(Base, TimestampMixin):
    __tablename__ = "failure_modes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(128), index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class RawMaintenanceEvent(Base):
    __tablename__ = "raw_maintenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_file_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    raw_fecha: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_linea: Mapped[str | None] = mapped_column(String(160), nullable=True)
    raw_turno: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_equipo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    raw_dano: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_razon: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_tiempo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_frecuencia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_anio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_mes: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_payload_json: Mapped[str] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(40), default="valid")
    validation_errors_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MaintenanceEvent(Base, TimestampMixin):
    __tablename__ = "maintenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_file_id: Mapped[int | None] = mapped_column(ForeignKey("uploaded_files.id"), index=True, nullable=True)
    event_hash: Mapped[str] = mapped_column(String(128), index=True)
    event_date: Mapped[date] = mapped_column(Date)
    production_line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"), index=True)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"), nullable=True, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), index=True)
    failure_mode_id: Mapped[int | None] = mapped_column(ForeignKey("failure_modes.id"), nullable=True, index=True)
    reported_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    damage_description: Mapped[str] = mapped_column(Text)
    reason_description: Mapped[str] = mapped_column(Text)
    raw_damage_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_reason_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    downtime_minutes: Mapped[float] = mapped_column(Float)
    frequency: Mapped[float] = mapped_column(Float)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default="confirmed")
    source: Mapped[str] = mapped_column(String(30), default="excel", index=True)
    corrected_from_raw_event_id: Mapped[int | None] = mapped_column(ForeignKey("raw_maintenance_events.id"), nullable=True)


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_file_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True)
    raw_event_id: Mapped[int | None] = mapped_column(ForeignKey("raw_maintenance_events.id"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(80))
    error_type: Mapped[str] = mapped_column(String(80))
    error_message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="open")
    resolved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportExport(Base):
    __tablename__ = "report_exports"

    id: Mapped[int] = mapped_column(primary_key=True)
    generated_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[str] = mapped_column(String(80))
    date_from: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    filters_json: Mapped[str] = mapped_column(Text, default="{}")
    file_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# PMP is intentionally independent from MaintenanceEvent.  A preventive order
# has a lifecycle and a planned workload; it is not a failure record.
class PmpArea(Base, TimestampMixin):
    __tablename__ = "pmp_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PmpImport(Base, TimestampMixin):
    __tablename__ = "pmp_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_filename: Mapped[str] = mapped_column(String(255))
    source_hash: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class PmpImportError(Base):
    __tablename__ = "pmp_import_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    pmp_import_id: Mapped[int] = mapped_column(ForeignKey("pmp_imports.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer, index=True)
    field_name: Mapped[str] = mapped_column(String(80))
    error_code: Mapped[str] = mapped_column(String(80))
    error_message: Mapped[str] = mapped_column(Text)
    raw_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PmpOrder(Base, TimestampMixin):
    __tablename__ = "pmp_orders"
    __table_args__ = (UniqueConstraint("external_id", name="uq_pmp_orders_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(160), index=True)
    pmp_area_id: Mapped[int] = mapped_column(ForeignKey("pmp_areas.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    planned_minutes: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(30), default="excel", index=True)
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pmp_import_id: Mapped[int | None] = mapped_column(ForeignKey("pmp_imports.id"), nullable=True, index=True)
    raw_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    area: Mapped[PmpArea] = relationship()


class PmpOrderHistory(Base):
    __tablename__ = "pmp_order_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    pmp_order_id: Mapped[int] = mapped_column(ForeignKey("pmp_orders.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PmpPersonnel(Base, TimestampMixin):
    __tablename__ = "pmp_personnel"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    pmp_area_id: Mapped[int] = mapped_column(ForeignKey("pmp_areas.id"), index=True)
    shift_name: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PmpWeeklySchedule(Base, TimestampMixin):
    __tablename__ = "pmp_weekly_schedules"
    __table_args__ = (UniqueConstraint("pmp_personnel_id", "week_start", name="uq_pmp_schedule_person_week"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pmp_personnel_id: Mapped[int] = mapped_column(ForeignKey("pmp_personnel.id"), index=True)
    pmp_area_id: Mapped[int] = mapped_column(ForeignKey("pmp_areas.id"), index=True)
    shift_name: Mapped[str] = mapped_column(String(20))
    week_start: Mapped[date] = mapped_column(Date, index=True)
    available_minutes: Mapped[float] = mapped_column(Float)


class PmpSnapshot(Base):
    __tablename__ = "pmp_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    metrics_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# These two tables reserve an auditable integration boundary.  Phase 1 does
# not store a token or make SAIM calls.
class PmpSaimConfig(Base, TimestampMixin):
    __tablename__ = "pmp_saim_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    encrypted_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PmpSyncExecution(Base):
    __tablename__ = "pmp_sync_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(40), default="not_started")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, default=0)
    safe_error: Mapped[str | None] = mapped_column(Text, nullable=True)
