import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid


from app.core.database import Base


class ComplaintSequence(Base):
    """Per-district, per-year counter backing human-readable complaint numbers."""

    __tablename__ = "complaint_sequences"

    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("districts.id", ondelete="RESTRICT"), primary_key=True
    )
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    last_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
