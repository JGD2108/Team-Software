"""normalize equipment taxonomy from code segments

Revision ID: 20260811_0005
Revises: 20260810_0004
Create Date: 2026-08-11
"""
from alembic import op


revision = "20260811_0005"
down_revision = "20260810_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        with taxonomy as (
            select
                id,
                string_to_array(code, '-') as segments,
                array_length(string_to_array(code, '-'), 1) as level
            from equipment
            where code is not null
        ), normalized as (
            select
                taxonomy.id,
                taxonomy.level,
                case when taxonomy.level >= 2 then array_to_string(taxonomy.segments[1:2], '-') end as area_code,
                case when taxonomy.level >= 3 then array_to_string(taxonomy.segments[1:3], '-') end as process_code,
                case when taxonomy.level > 1 then array_to_string(taxonomy.segments[1:taxonomy.level - 1], '-') end as parent_code
            from taxonomy
        )
        update equipment as target
        set
            hierarchy_level = normalized.level,
            parent_code = normalized.parent_code,
            area_code = normalized.area_code,
            area_name = area.name,
            process_code = normalized.process_code,
            process_name = process.name,
            production_line_id = production_line.id
        from normalized
        left join equipment as area on area.code = normalized.area_code and area.hierarchy_level = 2
        left join equipment as process on process.code = normalized.process_code and process.hierarchy_level = 3
        left join production_lines as production_line on production_line.code = normalized.area_code
        where target.id = normalized.id
        """
    )


def downgrade() -> None:
    # Source indentation is not recoverable from the normalized database.
    pass
