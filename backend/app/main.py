from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, catalogs, dashboard, reports, uploads
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import entities  # noqa: F401
from app.services.bootstrap import seed_initial_data

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auth.users_router)
app.include_router(catalogs.router)
app.include_router(uploads.router)
app.include_router(uploads.corrections_router)
app.include_router(dashboard.router)
app.include_router(dashboard.quality_router)
app.include_router(dashboard.audit_router)
app.include_router(reports.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)


@app.get("/health")
def health():
    return {"ok": True}
