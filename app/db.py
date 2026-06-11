from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_kwargs = {}

if settings.database_url.startswith("sqlite:///"):
    db_path_str = settings.database_url.removeprefix("sqlite:///")
    if db_path_str == ":memory:":
        # A single shared connection, so the in-memory DB is visible across
        # the threads TestClient/anyio use for request handling (tests only).
        engine_kwargs["poolclass"] = StaticPool
    else:
        Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import models  # noqa: F401  registers all tables on Base.metadata

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
