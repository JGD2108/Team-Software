from fastapi.testclient import TestClient

from app.api.deps import current_user
from app.main import app
from app.models import User


def test_pmp_orders_route_is_registered_and_protected():
    """The Vercel ASGI entrypoint must expose the dashboard drill-down route."""
    client = TestClient(app)

    response = client.get("/pmp/orders?offset=0&limit=30")

    # A missing route returns 404. This route intentionally requires the
    # existing bearer dependency, so an anonymous request is rejected first.
    assert response.status_code == 403
    operation = app.openapi()["paths"]["/pmp/orders"]["get"]
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "area",
        "status",
        "as_of_date",
        "date_from",
        "date_to",
        "offset",
        "limit",
    }


def test_pmp_orders_rejects_a_reversed_date_range_with_a_clear_400():
    app.dependency_overrides[current_user] = lambda: User(id=1, name="Test", email="test@example.com", password_hash="x", role="plant_user", is_active=True)
    try:
        response = TestClient(app).get("/pmp/orders?date_from=2026-08-12&date_to=2026-08-10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "fecha inicial" in response.json()["detail"].lower()
