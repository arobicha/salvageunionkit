"""Encounter table entry ORM."""
from __future__ import annotations

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.schema._base import Base


class EncounterEntryORM(Base):
    __tablename__ = "encounter_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("region.id", ondelete="CASCADE"), nullable=False
    )
    roll: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, default="")
    threat_id: Mapped[str] = mapped_column(String(36), default="")

    region: Mapped["RegionORM"] = relationship(back_populates="encounter_entries")  # noqa: F821
