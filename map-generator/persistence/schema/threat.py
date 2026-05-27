"""Threat ORM table."""
from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.schema._base import Base


class ThreatORM(Base):
    __tablename__ = "threat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    region_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("region.id", ondelete="CASCADE"), nullable=False
    )
    subtype: Mapped[str] = mapped_column(String(40), default="Tyrant")
    name: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    region: Mapped["RegionORM"] = relationship(back_populates="threats")  # noqa: F821
