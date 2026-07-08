"""initial schema

Revision ID: 20260708_0001
Revises:
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa

revision = "20260708_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "production_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_production_lines_name", "production_lines", ["name"], unique=True)
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("production_line_id", sa.Integer(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", "production_line_id", name="uq_equipment_line"),
    )
    op.create_index("ix_equipment_name", "equipment", ["name"])
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("error_rows", sa.Integer(), nullable=False),
        sa.Column("warning_rows", sa.Integer(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_uploaded_files_file_hash", "uploaded_files", ["file_hash"])
    op.create_table(
        "raw_maintenance_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uploaded_file_id", sa.Integer(), sa.ForeignKey("uploaded_files.id"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_fecha", sa.String(length=120), nullable=True),
        sa.Column("raw_linea", sa.String(length=160), nullable=True),
        sa.Column("raw_turno", sa.String(length=120), nullable=True),
        sa.Column("raw_equipo", sa.String(length=160), nullable=True),
        sa.Column("raw_dano", sa.Text(), nullable=True),
        sa.Column("raw_razon", sa.Text(), nullable=True),
        sa.Column("raw_tiempo", sa.String(length=120), nullable=True),
        sa.Column("raw_frecuencia", sa.String(length=120), nullable=True),
        sa.Column("raw_anio", sa.String(length=120), nullable=True),
        sa.Column("raw_mes", sa.String(length=120), nullable=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=False),
        sa.Column("validation_status", sa.String(length=40), nullable=False),
        sa.Column("validation_errors_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_raw_maintenance_events_uploaded_file_id", "raw_maintenance_events", ["uploaded_file_id"])
    op.create_table(
        "maintenance_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uploaded_file_id", sa.Integer(), sa.ForeignKey("uploaded_files.id"), nullable=False),
        sa.Column("event_hash", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("production_line_id", sa.Integer(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("shift_id", sa.Integer(), sa.ForeignKey("shifts.id"), nullable=True),
        sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("damage_description", sa.Text(), nullable=False),
        sa.Column("reason_description", sa.Text(), nullable=False),
        sa.Column("downtime_minutes", sa.Float(), nullable=False),
        sa.Column("frequency", sa.Float(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("corrected_from_raw_event_id", sa.Integer(), sa.ForeignKey("raw_maintenance_events.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_maintenance_events_uploaded_file_id", "maintenance_events", ["uploaded_file_id"])
    op.create_index("ix_maintenance_events_event_hash", "maintenance_events", ["event_hash"])
    op.create_table(
        "validation_errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uploaded_file_id", sa.Integer(), sa.ForeignKey("uploaded_files.id"), nullable=False),
        sa.Column("raw_event_id", sa.Integer(), sa.ForeignKey("raw_maintenance_events.id"), nullable=True),
        sa.Column("field_name", sa.String(length=80), nullable=False),
        sa.Column("error_type", sa.String(length=80), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_validation_errors_uploaded_file_id", "validation_errors", ["uploaded_file_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "report_exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("generated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_type", sa.String(length=80), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "report_exports",
        "audit_logs",
        "validation_errors",
        "maintenance_events",
        "raw_maintenance_events",
        "uploaded_files",
        "equipment",
        "shifts",
        "production_lines",
        "users",
    ]:
        op.drop_table(table)
