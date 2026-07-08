from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.services.bootstrap import seed_initial_data

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_initial_data(db)

client = TestClient(app)


def token(email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_plant_user_cannot_generate_pdf():
    access = token("planta@mantenimiento.local", "Planta123!")
    response = client.post("/reports/management-pdf", headers={"Authorization": f"Bearer {access}"}, json={})
    assert response.status_code == 403


def test_admin_can_list_users():
    access = token("admin@mantenimiento.local", "Admin123!")
    response = client.get("/users", headers={"Authorization": f"Bearer {access}"})
    assert response.status_code == 200
