"""persist PMP planned dates and query projections

Revision ID: 20260812_0008
Revises: 20260812_0007
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0008"
down_revision = "20260812_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pmp_imports", sa.Column("reconciliation_json", sa.Text(), nullable=True))
    op.add_column("pmp_orders", sa.Column("planned_start_date", sa.Date(), nullable=True))
    op.create_index(
        "ix_pmp_orders_active_area_status_date",
        "pmp_orders",
        ["is_active", "pmp_area_id", "status", "planned_start_date"],
    )
    op.create_index(
        "ix_pmp_orders_active_status_date",
        "pmp_orders",
        ["is_active", "status", "planned_start_date"],
    )
    op.create_index(
        "ix_pmp_orders_active_area_external",
        "pmp_orders",
        ["is_active", "pmp_area_id", "external_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pmp_orders_active_area_external", table_name="pmp_orders")
    op.drop_index("ix_pmp_orders_active_status_date", table_name="pmp_orders")
    op.drop_index("ix_pmp_orders_active_area_status_date", table_name="pmp_orders")
    op.drop_column("pmp_orders", "planned_start_date")
    op.drop_column("pmp_imports", "reconciliation_json")
