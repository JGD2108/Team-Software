from datetime import datetime

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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="production_line")


class Equipment(Base, TimestampMixin):
    __tablename__ = "equipment"
    __table_args__ = (UniqueConstraint("name", "production_line_id", name="uq_equipment_line"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    production_line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    production_line: Mapped[ProductionLine] = relationship(back_populates="equipment")


class Shift(Base, TimestampMixin):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
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
    uploaded_file_id: Mapped[int] = mapped_column(ForeignKey("uploaded_files.id"), index=True)
    event_hash: Mapped[str] = mapped_column(String(128), index=True)
    event_date: Mapped[datetime] = mapped_column(Date)
    production_line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"))
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"), nullable=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))
    damage_description: Mapped[str] = mapped_column(Text)
    reason_description: Mapped[str] = mapped_column(Text)
    downtime_minutes: Mapped[float] = mapped_column(Float)
    frequency: Mapped[float] = mapped_column(Float)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default="confirmed")
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
