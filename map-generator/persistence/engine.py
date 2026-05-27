"""SQLAlchemy engine + sessionmaker for the regions database."""
from __future__ import annotations
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from persistence.schema._base import Base
from persistence.schema import region as _region  # noqa: F401
from persistence.schema import area as _area      # noqa: F401
from persistence.schema import threat as _threat  # noqa: F401
from persistence.schema import settlement as _settlement  # noqa: F401
from persistence.schema import encounter as _encounter    # noqa: F401


def build_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
