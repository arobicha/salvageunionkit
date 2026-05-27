"""Settlement ORM table."""
from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.schema._base import Base


class SettlementORM(Base):
    __tablename__ = "settlement"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    region_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("region.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), default="")
    feature: Mapped[str] = mapped_column(Text, default="")
    linked_threat_id: Mapped[str] = mapped_column(String(36), default="")

    region: Mapped["RegionORM"] = relationship(back_populates="settlements")  # noqa: F821
