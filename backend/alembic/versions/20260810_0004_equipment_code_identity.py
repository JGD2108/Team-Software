"""use taxonomy code as equipment identity

Revision ID: 20260810_0004
Revises: 20260810_0003
Create Date: 2026-08-10
"""
from alembic import op


revision = "20260810_0004"
down_revision = "20260810_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_equipment_line", "equipment", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_equipment_line", "equipment", ["name", "production_line_id"])
