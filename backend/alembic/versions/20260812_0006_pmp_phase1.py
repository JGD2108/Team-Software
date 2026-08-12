"""add independent PMP phase 1 tables

Revision ID: 20260812_0006
Revises: 20260811_0005
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0006"
down_revision = "20260811_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("pmp_areas", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_pmp_areas_name", "pmp_areas", ["name"], unique=True)
    op.create_table("pmp_imports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_filename", sa.String(255), nullable=False), sa.Column("source_hash", sa.String(128), nullable=False), sa.Column("status", sa.String(40), nullable=False), sa.Column("total_rows", sa.Integer(), nullable=False), sa.Column("valid_rows", sa.Integer(), nullable=False), sa.Column("invalid_rows", sa.Integer(), nullable=False), sa.Column("reconciled_at", sa.DateTime()), sa.Column("approved_at", sa.DateTime()), sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_pmp_imports_source_hash", "pmp_imports", ["source_hash"])
    op.create_table("pmp_import_errors", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("pmp_import_id", sa.Integer(), sa.ForeignKey("pmp_imports.id"), nullable=False), sa.Column("row_number", sa.Integer(), nullable=False), sa.Column("field_name", sa.String(80), nullable=False), sa.Column("error_code", sa.String(80), nullable=False), sa.Column("error_message", sa.Text(), nullable=False), sa.Column("raw_payload_json", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_pmp_import_errors_import", "pmp_import_errors", ["pmp_import_id"])
    op.create_table("pmp_orders", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("external_id", sa.String(160), nullable=False), sa.Column("pmp_area_id", sa.Integer(), sa.ForeignKey("pmp_areas.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("planned_minutes", sa.Float(), nullable=False), sa.Column("source", sa.String(30), nullable=False), sa.Column("source_row_number", sa.Integer()), sa.Column("pmp_import_id", sa.Integer(), sa.ForeignKey("pmp_imports.id")), sa.Column("raw_payload_json", sa.Text(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("external_id", name="uq_pmp_orders_external_id"))
    op.create_index("ix_pmp_orders_external_id", "pmp_orders", ["external_id"])
    op.create_index("ix_pmp_orders_area", "pmp_orders", ["pmp_area_id"])
    op.create_table("pmp_order_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("pmp_order_id", sa.Integer(), sa.ForeignKey("pmp_orders.id"), nullable=False), sa.Column("action", sa.String(80), nullable=False), sa.Column("before_json", sa.Text()), sa.Column("after_json", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("pmp_personnel", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("pmp_area_id", sa.Integer(), sa.ForeignKey("pmp_areas.id"), nullable=False), sa.Column("shift_name", sa.String(20), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("pmp_weekly_schedules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("pmp_personnel_id", sa.Integer(), sa.ForeignKey("pmp_personnel.id"), nullable=False), sa.Column("pmp_area_id", sa.Integer(), sa.ForeignKey("pmp_areas.id"), nullable=False), sa.Column("shift_name", sa.String(20), nullable=False), sa.Column("week_start", sa.Date(), nullable=False), sa.Column("available_minutes", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("pmp_personnel_id", "week_start", name="uq_pmp_schedule_person_week"))
    op.create_table("pmp_snapshots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("snapshot_date", sa.Date(), nullable=False), sa.Column("metrics_json", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("pmp_saim_config", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("encrypted_token", sa.Text()), sa.Column("token_updated_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("pmp_sync_executions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("status", sa.String(40), nullable=False), sa.Column("started_at", sa.DateTime(), nullable=False), sa.Column("completed_at", sa.DateTime()), sa.Column("received_count", sa.Integer(), nullable=False), sa.Column("valid_count", sa.Integer(), nullable=False), sa.Column("safe_error", sa.Text()))


def downgrade() -> None:
    for table in ("pmp_sync_executions", "pmp_saim_config", "pmp_snapshots", "pmp_weekly_schedules", "pmp_personnel", "pmp_order_history", "pmp_orders", "pmp_import_errors", "pmp_imports", "pmp_areas"):
        op.drop_table(table)
