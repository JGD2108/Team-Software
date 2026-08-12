import gzip
import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Equipment, ProductionLine


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "equipment_catalog.json.gz"


def seed_equipment_catalog(db: Session) -> bool:
    """Load the normalized source catalog once, preserving historical rows."""
    if not CATALOG_PATH.exists() or db.query(Equipment.id).filter(Equipment.code == "BA").first():
        return False

    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as handle:
        catalog = json.load(handle)

    # The code is the authoritative taxonomy. Some source rows were nested
    # under the wrong visual parent in the spreadsheet, so always derive area
    # and process from BA-AREA-LINE instead of trusting that indentation.
    area_names = {row["code"]: row["name"] for row in catalog if row["hierarchy_level"] == 2}
    process_names = {row["code"]: row["name"] for row in catalog if row["hierarchy_level"] == 3}

    # Historical catalog rows remain available to old reports but stop appearing
    # in new report selectors after the authoritative taxonomy is loaded.
    db.query(Equipment).filter(Equipment.code.is_(None)).update(
        {Equipment.is_active: False, Equipment.is_reportable: False},
        synchronize_session=False,
    )
    db.query(ProductionLine).filter(ProductionLine.code.is_(None)).update(
        {ProductionLine.is_active: False},
        synchronize_session=False,
    )

    line_ids: dict[str, int] = {}
    for area in (row for row in catalog if row["hierarchy_level"] == 2):
        line = db.query(ProductionLine).filter(ProductionLine.code == area["code"]).first()
        if not line:
            line = db.query(ProductionLine).filter(func.lower(ProductionLine.name) == area["name"].lower()).first()
        if not line:
            line = ProductionLine(name=area["name"], code=area["code"], is_active=area["is_active"])
            db.add(line)
        else:
            line.name = area["name"]
            line.code = area["code"]
            line.is_active = area["is_active"]
        db.flush()
        line_ids[area["code"]] = line.id

    mappings = []
    for row in catalog:
        mapping = dict(row)
        segments = mapping["code"].split("-")
        area_code = "-".join(segments[:2]) if len(segments) >= 2 else None
        process_code = "-".join(segments[:3]) if len(segments) >= 3 else None
        mapping["parent_code"] = "-".join(segments[:-1]) if len(segments) > 1 else None
        mapping["hierarchy_level"] = len(segments)
        mapping["area_code"] = area_code
        mapping["area_name"] = area_names.get(area_code)
        mapping["process_code"] = process_code
        mapping["process_name"] = process_names.get(process_code)
        mapping["production_line_id"] = line_ids.get(area_code)
        mappings.append(mapping)
    db.bulk_insert_mappings(Equipment, mappings, render_nulls=True)
    db.commit()
    return True
