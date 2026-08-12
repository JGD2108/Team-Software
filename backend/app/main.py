from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, catalogs, daily_reports, dashboard, pmp, reports, uploads
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import entities  # noqa: F401
from app.services.bootstrap import seed_initial_data
from app.services.equipment_catalog import seed_equipment_catalog

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
app.include_router(daily_reports.router)
app.include_router(uploads.router)
app.include_router(uploads.corrections_router)
app.include_router(dashboard.router)
app.include_router(dashboard.quality_router)
app.include_router(dashboard.audit_router)
app.include_router(reports.router)
app.include_router(pmp.router)


@app.on_event("startup")
def startup() -> None:
    # Supabase schema is managed through migrations. Keeping create_all for
    # local databases preserves the existing development workflow.
    if "supabase" not in settings.database_url:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if "supabase" in settings.database_url:
            # Serverless instances can start concurrently. Serialize the seed
            # operation so unique catalog rows are only created once.
            db.execute(text("select pg_advisory_xact_lock(842119)"))
        seed_initial_data(db)
        if "supabase" in settings.database_url:
            db.execute(text("select pg_advisory_xact_lock(842120)"))
            seed_equipment_catalog(db)


@app.get("/health")
def health():
    return {"ok": True}
