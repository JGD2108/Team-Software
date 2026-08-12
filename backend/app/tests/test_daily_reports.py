from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.services.bootstrap import seed_initial_data


Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_initial_data(db)

client = TestClient(app)


def auth(email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


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
    assert isinstance(client.get(f"/daily-reports?report_date={report_date.isoformat()}", headers=headers).json(), list)
    return
    body = response.json()
    assert body["event_date"] == report_date.isoformat()
    assert body["damage_description"] == "RODAMIENTO DEL MOTOR"
    assert body["reason_description"] == "FALTA DE LUBRICACI\u00d3N"
    assert "area_code" in body
    assert "process_code" in body
    assert "equipment_code" in body
    reports_for_day = client.get(f"/daily-reports?report_date={body['event_date']}", headers=headers)
    assert reports_for_day.status_code == 200
    assert any(report["id"] == body["id"] for report in reports_for_day.json())
    assert client.get("/daily-reports?report_date=2000-01-01", headers=headers).json() == []

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
