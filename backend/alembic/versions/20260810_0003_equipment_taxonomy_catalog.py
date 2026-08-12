"""equipment taxonomy catalog

Revision ID: 20260810_0003
Revises: 20260810_0002
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa


revision = "20260810_0003"
down_revision = "20260810_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("production_lines", sa.Column("code", sa.String(length=40), nullable=True))
    op.create_index("ix_production_lines_code", "production_lines", ["code"], unique=True)
    op.alter_column("equipment", "name", existing_type=sa.String(length=160), type_=sa.String(length=500), nullable=False)
    op.alter_column("equipment", "production_line_id", existing_type=sa.Integer(), nullable=True)
    columns = [
        sa.Column("code", sa.String(length=120), nullable=True),
        sa.Column("parent_code", sa.String(length=120), nullable=True),
        sa.Column("hierarchy_level", sa.Integer(), nullable=True),
        sa.Column("plant_code", sa.String(length=20), nullable=True),
        sa.Column("plant_name", sa.String(length=160), nullable=True),
        sa.Column("area_code", sa.String(length=40), nullable=True),
        sa.Column("area_name", sa.String(length=200), nullable=True),
        sa.Column("process_code", sa.String(length=80), nullable=True),
        sa.Column("process_name", sa.String(length=300), nullable=True),
        sa.Column("is_reportable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("brand", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("qr_code", sa.String(length=80), nullable=True),
        sa.Column("criticality", sa.String(length=10), nullable=True),
        sa.Column("specialty", sa.String(length=30), nullable=True),
        sa.Column("grouping", sa.String(length=80), nullable=True),
        sa.Column("analysis_group", sa.String(length=80), nullable=True),
        sa.Column("pdt_group", sa.String(length=80), nullable=True),
        sa.Column("source_status", sa.String(length=40), nullable=True),
        sa.Column("financial_code", sa.String(length=80), nullable=True),
        sa.Column("cost_center", sa.String(length=80), nullable=True),
    ]
    for column in columns:
        op.add_column("equipment", column)
    for column in ["code", "hierarchy_level", "area_code", "process_code", "is_reportable", "criticality", "specialty"]:
        op.create_index(f"ix_equipment_{column}", "equipment", [column], unique=column == "code")
    op.create_index("ix_equipment_catalog_filters", "equipment", ["area_code", "process_code", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_equipment_catalog_filters", table_name="equipment")
    for column in ["specialty", "criticality", "is_reportable", "process_code", "area_code", "hierarchy_level", "code"]:
        op.drop_index(f"ix_equipment_{column}", table_name="equipment")
    for column in [
        "cost_center", "financial_code", "source_status", "pdt_group", "analysis_group", "grouping", "specialty",
        "criticality", "qr_code", "location", "serial_number", "model", "brand", "is_reportable", "process_name",
        "process_code", "area_name", "area_code", "plant_name", "plant_code", "hierarchy_level", "parent_code", "code",
    ]:
        op.drop_column("equipment", column)
    op.alter_column("equipment", "production_line_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("equipment", "name", existing_type=sa.String(length=500), type_=sa.String(length=160), nullable=False)
    op.drop_index("ix_production_lines_code", table_name="production_lines")
    op.drop_column("production_lines", "code")
