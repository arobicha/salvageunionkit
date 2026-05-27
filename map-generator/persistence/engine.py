"""SQLAlchemy engine + sessionmaker for the regions database."""
from __future__ import annotations
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from persistence.schema._base import Base
from persistence.schema import region as _region  # noqa: F401
from persistence.schema import area as _area      # noqa: F401
from persistence.schema import threat as _threat  # noqa: F401
from persistence.schema import settlement as _settlement  # noqa: F401
from persistence.schema import encounter as _encounter    # noqa: F401

_ADDITIVE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "area": [
        ("background_image", "BLOB"),
        ("background_native_w", "INTEGER NOT NULL DEFAULT 0"),
        ("background_native_h", "INTEGER NOT NULL DEFAULT 0"),
    ],
}


def build_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    _apply_additive_migrations(engine)
    return engine


def _apply_additive_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    for table, cols in _ADDITIVE_COLUMNS.items():
        if not inspector.has_table(table):
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        with engine.begin() as conn:
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
