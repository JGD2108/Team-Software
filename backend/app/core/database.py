from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
database_url = settings.database_url
# Supabase exposes standard postgresql:// connection strings.  SQLAlchemy maps
# that bare scheme to psycopg2 by default, while this service deliberately
# installs psycopg v3.  Make the runtime driver explicit without changing the
# deploy-time secret or SQLite fallback behavior.
if database_url.startswith("postgresql://"):
    database_url = f"postgresql+psycopg://{database_url.removeprefix('postgresql://')}"
elif database_url.startswith("postgres://"):
    database_url = f"postgresql+psycopg://{database_url.removeprefix('postgres://')}"

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine_options = {"pool_pre_ping": True, "connect_args": connect_args}
if "pooler.supabase.com" in database_url:
    # Vercel functions are short-lived; let Supabase's transaction pooler
    # manage connections instead of retaining a process-local pool.
    engine_options["poolclass"] = NullPool
    engine_options["connect_args"] = {**connect_args, "prepare_threshold": None}
engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
