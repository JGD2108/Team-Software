from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models import AuditLog, Equipment, FailureMode, MaintenanceEvent, ProductionLine, Shift, User
from app.services.bootstrap import seed_initial_data


Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_initial_data(db)

client = TestClient(app)


def auth(email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_manual_report(event_date: date) -> int:
    with SessionLocal() as db:
        line = db.query(ProductionLine).first()
        equipment = db.query(Equipment).filter(Equipment.production_line_id == line.id).first()
        shift = db.query(Shift).first()
        failure_mode = db.query(FailureMode).first()
        reporter = db.query(User).filter(User.email == "admin@mantenimiento.local").one()
        event = MaintenanceEvent(
            event_hash=uuid4().hex,
            event_date=event_date,
            production_line_id=line.id,
            shift_id=shift.id,
            equipment_id=equipment.id,
            failure_mode_id=failure_mode.id,
            reported_by_user_id=reporter.id,
            damage_description="DAÑO DE PRUEBA",
            reason_description="RAZÓN DE PRUEBA",
            downtime_minutes=15,
            frequency=1,
            year=event_date.year,
            month=event_date.month,
            status="confirmed",
            source="manual_report",
        )
        db.add(event)
        db.commit()
        return event.id


def test_manual_daily_report_creation_is_disabled():
    headers = auth("planta@mantenimiento.local", "Planta123!")
    equipment = client.get("/equipment?include_inactive=false", headers=headers).json()[0]
    shift = client.get("/shifts", headers=headers).json()[0]
    failure_mode = client.get("/failure-modes?include_inactive=false", headers=headers).json()[0]
    report_date = datetime.now(ZoneInfo("America/Bogota")).date() - timedelta(days=1)
    response = client.post(
        "/daily-reports",
        headers=headers,
        json={
            "event_date": report_date.isoformat(),
            "production_line_id": equipment["production_line_id"],
            "shift_id": shift["id"],
            "equipment_id": equipment["id"],
            "failure_mode_id": failure_mode["id"],
            "damage_description": "  rodamiento   del motor ",
            "reason_description": " falta de   lubricaci\u00f3n ",
            "downtime_minutes": 25.5,
            "frequency": 2,
        },
    )
    assert response.status_code == 410
    assert "retirado" in response.json()["detail"]
    assert isinstance(client.get(f"/daily-reports?date_from={report_date.isoformat()}&date_to={report_date.isoformat()}", headers=headers).json(), list)
    return
    body = response.json()
    assert body["event_date"] == report_date.isoformat()
    assert body["damage_description"] == "RODAMIENTO DEL MOTOR"
    assert body["reason_description"] == "FALTA DE LUBRICACI\u00d3N"
    assert "area_code" in body
    assert "process_code" in body
    assert "equipment_code" in body
    reports_for_day = client.get(f"/daily-reports?date_from={body['event_date']}&date_to={body['event_date']}", headers=headers)
    assert reports_for_day.status_code == 200
    assert any(report["id"] == body["id"] for report in reports_for_day.json())
    assert client.get("/daily-reports?date_from=2000-01-01&date_to=2000-01-01", headers=headers).json() == []

    future_response = client.post(
        "/daily-reports",
        headers=headers,
        json={
            "event_date": (datetime.now(ZoneInfo("America/Bogota")).date() + timedelta(days=1)).isoformat(),
            "production_line_id": equipment["production_line_id"],
            "shift_id": shift["id"],
            "equipment_id": equipment["id"],
            "failure_mode_id": failure_mode["id"],
            "damage_description": "Rodamiento del motor",
            "reason_description": "Falta de lubricación",
            "downtime_minutes": 10,
            "frequency": 1,
        },
    )
    assert future_response.status_code == 400
    assert future_response.json()["detail"] == "La fecha del reporte no puede ser futura"


def test_only_admin_can_add_failure_mode():
    mode_name = f"FALLA PRUEBA {uuid4().hex[:8]}"
    plant_headers = auth("planta@mantenimiento.local", "Planta123!")
    denied = client.post("/failure-modes", headers=plant_headers, json={"name": mode_name})
    assert denied.status_code == 403

    admin_headers = auth("admin@mantenimiento.local", "Admin123!")
    created = client.post("/failure-modes", headers=admin_headers, json={"name": mode_name.lower()})
    assert created.status_code == 200
    assert created.json()["name"] == mode_name.upper()


def test_admin_can_delete_a_single_manual_report_and_audits_it():
    report_id = create_manual_report(date(2026, 8, 10))
    response = client.delete(f"/daily-reports/{report_id}", headers=auth("admin@mantenimiento.local", "Admin123!"))

    assert response.status_code == 200
    assert response.json() == {"id": report_id, "deleted": True}
    with SessionLocal() as db:
        assert db.get(MaintenanceEvent, report_id) is None
        audit = db.query(AuditLog).filter(AuditLog.entity_id == report_id, AuditLog.action == "daily_report_delete").one()
        assert audit.before_json is not None


def test_delete_daily_report_requires_admin_permission():
    report_id = create_manual_report(date(2026, 8, 11))
    response = client.delete(f"/daily-reports/{report_id}", headers=auth("planta@mantenimiento.local", "Planta123!"))

    assert response.status_code == 403
    with SessionLocal() as db:
        assert db.get(MaintenanceEvent, report_id) is not None


def test_delete_daily_report_requires_authentication():
    response = client.delete("/daily-reports/999999")
    assert response.status_code == 403


def test_delete_daily_report_returns_404_for_missing_manual_report():
    response = client.delete("/daily-reports/999999", headers=auth("admin@mantenimiento.local", "Admin123!"))
    assert response.status_code == 404
    assert response.json()["detail"] == "Reporte diario no encontrado"


def test_daily_report_range_is_inclusive():
    first_id = create_manual_report(date(2026, 8, 20))
    middle_id = create_manual_report(date(2026, 8, 21))
    last_id = create_manual_report(date(2026, 8, 22))

    response = client.get(
        "/daily-reports?date_from=2026-08-20&date_to=2026-08-22",
        headers=auth("admin@mantenimiento.local", "Admin123!"),
    )

    assert response.status_code == 200
    returned_ids = {report["id"] for report in response.json()}
    assert {first_id, middle_id, last_id}.issubset(returned_ids)


def test_daily_report_range_rejects_reversed_dates():
    response = client.get(
        "/daily-reports?date_from=2026-08-22&date_to=2026-08-20",
        headers=auth("admin@mantenimiento.local", "Admin123!"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La fecha inicial no puede ser posterior a la fecha final"


def test_daily_report_range_returns_empty_list_when_no_records_match():
    response = client.get(
        "/daily-reports?date_from=2000-01-01&date_to=2000-01-02",
        headers=auth("admin@mantenimiento.local", "Admin123!"),
    )

    assert response.status_code == 200
    assert response.json() == []
