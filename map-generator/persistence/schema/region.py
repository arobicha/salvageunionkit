"""Region ORM table."""
from __future__ import annotations
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.schema._base import Base


class RegionORM(Base):
    __tablename__ = "region"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    core_feature: Mapped[str] = mapped_column(Text, default="")
    terrain_type: Mapped[str] = mapped_column(String(120), default="")
    tech_level: Mapped[int] = mapped_column(Integer, default=1)
    max_scrap_budget: Mapped[int] = mapped_column(Integer, default=0)
    gm_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    areas: Mapped[list["AreaORM"]] = relationship(  # noqa: F821
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    threats: Mapped[list["ThreatORM"]] = relationship(  # noqa: F821
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    settlements: Mapped[list["SettlementORM"]] = relationship(  # noqa: F821
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    encounter_entries: Mapped[list["EncounterEntryORM"]] = relationship(  # noqa: F821
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
