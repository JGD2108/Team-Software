import json
from datetime import date
from pathlib import Path

from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import PmpArea, PmpOrder, PmpPersonnel, PmpWeeklySchedule
from app.services.pmp import capacity_metrics, dashboard_metrics, import_jose_workbook, list_orders, reconcile_import


def fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add_order(db, area: PmpArea, external_id: str, status: str, minutes: float, planned_start: str = "2026-08-10 13:00:00.000"):
    db.add(PmpOrder(
        external_id=external_id,
        pmp_area_id=area.id,
        status=status,
        planned_minutes=minutes,
        source="excel",
        raw_payload_json=json.dumps({"3": planned_start}),
    ))


def test_jose_import_reconciles_real_workbook_and_direct_database_aggregation():
    db = fresh_session()
    imported = import_jose_workbook(db, Path(__file__).resolve().parents[3] / "backend" / "app" / "data" / "JOSE.xlsx")
    reconciliation = reconcile_import(db, imported)
    direct_orders, direct_minutes = db.query(func.count(PmpOrder.id), func.sum(PmpOrder.planned_minutes)).one()

    assert (imported.total_rows, imported.valid_rows, imported.invalid_rows) == (1082, 1009, 73)
    assert reconciliation["matches"] is True
    assert reconciliation["persisted"]["global"]["planned_minutes"] == 53874.0
    assert (direct_orders, direct_minutes) == (1009, 53874.0)
    assert reconciliation["persisted"]["by_area"]["ELE"]["orders"] == 538


def test_metrics_keep_orders_minutes_and_hours_separate_by_area():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    add_order(db, area, "OT-1", "finalized", 120)
    add_order(db, area, "OT-2", "pending", 60)
    db.commit()

    metric = dashboard_metrics(db)["by_area"]["MEC"]

    assert metric["total_orders"] == 2
    assert metric["finalized_orders"] == 1
    assert metric["pending_orders"] == 1
    assert metric["planned_minutes"] == 180
    assert metric["planned_hours"] == 3
    assert metric["completed_planned_hours"] == 2
    assert metric["pending_planned_hours"] == 1
    assert metric["workload_completion_percent"] == 66.67
    assert metric["order_completion_percent"] == 50


def test_compliance_at_exactly_ninety_is_not_compliant_and_is_yellow():
    db = fresh_session()
    area = PmpArea(name="ELE")
    db.add(area)
    db.flush()
    for number in range(10):
        add_order(db, area, f"OT-{number}", "finalized" if number < 9 else "pending", 60)
    db.commit()

    metrics = dashboard_metrics(db)["global"]

    assert metrics["workload_completion_percent"] == 90.0
    assert metrics["order_completion_percent"] == 90.0
    assert metrics["compliant"] is False
    assert metrics["traffic_light"] == "yellow"
    assert metrics["additional_completed_minutes_lower_bound"] == 0.0
    assert "90 % exacto no cumple" in metrics["strict_target_note"]


def test_filters_use_real_planned_start_date_and_status_without_n_plus_one_behavior():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    add_order(db, area, "OT-old", "finalized", 60, "2026-08-09 07:00:00.000")
    add_order(db, area, "OT-new", "pending", 120, "2026-08-11 07:00:00.000")
    db.commit()

    metrics = dashboard_metrics(db, "MEC", "finalized", date(2026, 8, 10))
    orders = list_orders(db, "MEC", None, date(2026, 8, 10))

    assert metrics["global"]["total_orders"] == 1
    assert metrics["global"]["planned_minutes"] == 60
    assert metrics["filter_application"]["order_date_filter"] == "planned_start_date_from_excel"
    assert [item["external_id"] for item in orders["items"]] == ["OT-old"]


def test_area_without_orders_returns_zero_metrics():
    db = fresh_session()
    db.add(PmpArea(name="SER"))
    db.commit()

    metrics = dashboard_metrics(db, "SER")

    assert metrics["global"]["total_orders"] == 0
    assert metrics["by_area"]["SER"]["pending_planned_hours"] == 0
    assert metrics["by_area"]["SER"]["compliant"] is False


def test_capacity_is_explicitly_unavailable_without_personnel_and_schedule():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    add_order(db, area, "OT-1", "pending", 600)
    db.commit()

    capacity = capacity_metrics(db, date(2026, 8, 10), dashboard_metrics(db))
    row = capacity["rows"][0]

    assert capacity["configured"] is False
    assert row["status"] == "not_configured"
    assert row["available_hours"] is None
    assert "personal PMP activo" in row["missing_inputs"]


def test_capacity_compares_real_schedule_to_pending_workload_and_staffing_gap():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    add_order(db, area, "OT-1", "pending", 600)
    person = PmpPersonnel(name="Ana", pmp_area_id=area.id, shift_name="1")
    db.add(person)
    db.flush()
    db.add(PmpWeeklySchedule(pmp_personnel_id=person.id, pmp_area_id=area.id, shift_name="1", week_start=date(2026, 8, 10), available_minutes=300))
    db.commit()

    capacity = capacity_metrics(db, date(2026, 8, 10), dashboard_metrics(db))
    row = capacity["rows"][0]

    assert capacity["configured"] is True
    assert row["available_minutes"] == 300.0
    assert row["required_minutes"] == 600.0
    assert row["gap_minutes"] == 300.0
    assert row["staffing_gap_equivalent"] == 1.0
    assert row["status"] == "insufficient"


def test_shift_capacity_does_not_invent_shift_demand_assignment():
    db = fresh_session()
    area = PmpArea(name="MEC")
    db.add(area)
    db.flush()
    add_order(db, area, "OT-1", "pending", 120)
    person = PmpPersonnel(name="Ana", pmp_area_id=area.id, shift_name="1")
    db.add(person)
    db.flush()
    db.add(PmpWeeklySchedule(pmp_personnel_id=person.id, pmp_area_id=area.id, shift_name="1", week_start=date(2026, 8, 10), available_minutes=300))
    db.commit()

    capacity = capacity_metrics(db, date(2026, 8, 10), dashboard_metrics(db), shift_name="1")
    row = capacity["rows"][0]

    assert row["available_minutes"] == 300.0
    assert row["required_minutes"] is None
    assert row["status"] == "demand_not_assigned_to_shift"
