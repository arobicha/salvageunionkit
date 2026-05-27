"""Area ORM table."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Integer, Text, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from persistence.schema._base import Base


class AreaORM(Base):
    __tablename__ = "area"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    region_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("region.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    is_salvage: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starting: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_threat_id: Mapped[str] = mapped_column(String(36), default="")
    scrap_budget: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    point_crawl_json: Mapped[str] = mapped_column(Text, default="")
    background_image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True, default=None)
    background_native_w: Mapped[int] = mapped_column(Integer, default=0)
    background_native_h: Mapped[int] = mapped_column(Integer, default=0)

    region: Mapped["RegionORM"] = relationship(back_populates="areas")  # noqa: F821
