from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import PmpArea, PmpOrder, PmpPersonnel, PmpWeeklySchedule
from app.services.pmp import capacity_metrics, dashboard_metrics, import_jose_workbook, reconcile_import


def fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_jose_import_reconciles_real_workbook_totals():
    db = fresh_session()
    imported = import_jose_workbook(db, Path(__file__).resolve().parents[3] / "añadidos" / "JOSE.xlsx")
    reconciliation = reconcile_import(db, imported)
    assert (imported.total_rows, imported.valid_rows, imported.invalid_rows) == (1082, 1009, 73)
    assert reconciliation["matches"] is True
    assert reconciliation["persisted"]["global"]["planned_minutes"] == 53874.0
    assert reconciliation["persisted"]["by_area"]["ELE"]["orders"] == 538


def test_compliance_at_exactly_ninety_is_not_compliant():
    db = fresh_session()
    area = PmpArea(name="ELE")
    db.add(area)
    db.flush()
    for number in range(10):
        db.add(PmpOrder(external_id=f"OT-{number}", pmp_area_id=area.id, status="finalized" if number < 9 else "pending", planned_minutes=60, source="excel", raw_payload_json="{}"))
    db.commit()
    metrics = dashboard_metrics(db)
    assert metrics["global"]["compliance_percent"] == 90.0
    assert metrics["global"]["compliant"] is False
    assert metrics["global"]["traffic_light"] == "red"


def test_capacity_gap_and_fte_use_scheduled_minutes_per_shift():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    db.add(PmpOrder(external_id="OT-1", pmp_area_id=area.id, status="pending", planned_minutes=600, source="excel", raw_payload_json="{}"))
    person = PmpPersonnel(name="Ana", pmp_area_id=area.id, shift_name="1")
    db.add(person)
    db.flush()
    db.add(PmpWeeklySchedule(pmp_personnel_id=person.id, pmp_area_id=area.id, shift_name="1", week_start=date(2026, 8, 10), available_minutes=300))
    db.commit()
    capacity = capacity_metrics(db, date(2026, 8, 10))
    assert capacity[0]["gap_minutes"] == 300.0
    assert capacity[0]["fte_required"] == 1.0
    assert capacity[0]["alert"] is True
