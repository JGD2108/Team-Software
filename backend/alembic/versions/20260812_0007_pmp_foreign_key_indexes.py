"""add missing indexes for PMP foreign-key lookups

Revision ID: 20260812_0007
Revises: 20260812_0006
Create Date: 2026-08-12
"""

from alembic import op


revision = "20260812_0007"
down_revision = "20260812_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_pmp_imports_approved_by_user", "pmp_imports", ["approved_by_user_id"])
    op.create_index("ix_pmp_orders_import", "pmp_orders", ["pmp_import_id"])
    op.create_index("ix_pmp_order_history_order", "pmp_order_history", ["pmp_order_id"])
    op.create_index("ix_pmp_personnel_area", "pmp_personnel", ["pmp_area_id"])
    op.create_index("ix_pmp_weekly_schedules_person", "pmp_weekly_schedules", ["pmp_personnel_id"])
    op.create_index("ix_pmp_weekly_schedules_area", "pmp_weekly_schedules", ["pmp_area_id"])


def downgrade() -> None:
    op.drop_index("ix_pmp_weekly_schedules_area", table_name="pmp_weekly_schedules")
    op.drop_index("ix_pmp_weekly_schedules_person", table_name="pmp_weekly_schedules")
    op.drop_index("ix_pmp_personnel_area", table_name="pmp_personnel")
    op.drop_index("ix_pmp_order_history_order", table_name="pmp_order_history")
    op.drop_index("ix_pmp_orders_import", table_name="pmp_orders")
    op.drop_index("ix_pmp_imports_approved_by_user", table_name="pmp_imports")
