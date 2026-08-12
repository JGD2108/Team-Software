"""daily maintenance reports and failure modes

Revision ID: 20260810_0002
Revises: 20260708_0001
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "20260810_0002"
down_revision = "20260708_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "failure_modes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_failure_modes_name", "failure_modes", ["name"], unique=True)
    op.alter_column("maintenance_events", "uploaded_file_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("maintenance_events", sa.Column("failure_mode_id", sa.Integer(), nullable=True))
    op.add_column("maintenance_events", sa.Column("reported_by_user_id", sa.Integer(), nullable=True))
    op.add_column("maintenance_events", sa.Column("raw_damage_description", sa.Text(), nullable=True))
    op.add_column("maintenance_events", sa.Column("raw_reason_description", sa.Text(), nullable=True))
    op.add_column("maintenance_events", sa.Column("source", sa.String(length=30), nullable=False, server_default="excel"))
    op.create_foreign_key("fk_maintenance_events_failure_mode", "maintenance_events", "failure_modes", ["failure_mode_id"], ["id"])
    op.create_foreign_key("fk_maintenance_events_reported_by", "maintenance_events", "users", ["reported_by_user_id"], ["id"])
    op.create_index("ix_maintenance_events_failure_mode_id", "maintenance_events", ["failure_mode_id"])
    op.create_index("ix_maintenance_events_reported_by_user_id", "maintenance_events", ["reported_by_user_id"])
    op.create_index("ix_equipment_production_line_id", "equipment", ["production_line_id"])
    op.create_index("ix_maintenance_events_production_line_id", "maintenance_events", ["production_line_id"])
    op.create_index("ix_maintenance_events_shift_id", "maintenance_events", ["shift_id"])
    op.create_index("ix_maintenance_events_equipment_id", "maintenance_events", ["equipment_id"])
    op.create_index("ix_maintenance_events_source", "maintenance_events", ["source"])
    op.create_index("ix_maintenance_events_daily_reports", "maintenance_events", ["event_date", "source"])


def downgrade() -> None:
    for index in ["ix_maintenance_events_daily_reports", "ix_maintenance_events_source", "ix_maintenance_events_equipment_id", "ix_maintenance_events_shift_id", "ix_maintenance_events_production_line_id", "ix_equipment_production_line_id"]:
        op.drop_index(index, table_name="equipment" if index == "ix_equipment_production_line_id" else "maintenance_events")
    op.drop_index("ix_maintenance_events_reported_by_user_id", table_name="maintenance_events")
    op.drop_index("ix_maintenance_events_failure_mode_id", table_name="maintenance_events")
    op.drop_constraint("fk_maintenance_events_reported_by", "maintenance_events", type_="foreignkey")
    op.drop_constraint("fk_maintenance_events_failure_mode", "maintenance_events", type_="foreignkey")
    for column in ["source", "raw_reason_description", "raw_damage_description", "reported_by_user_id", "failure_mode_id"]:
        op.drop_column("maintenance_events", column)
    op.alter_column("maintenance_events", "uploaded_file_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_failure_modes_name", table_name="failure_modes")
    op.drop_table("failure_modes")
