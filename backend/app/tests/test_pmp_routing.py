from fastapi.testclient import TestClient

from app.main import app


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
        "offset",
        "limit",
    }
