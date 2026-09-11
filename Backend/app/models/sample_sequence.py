"""Global sequence counter for sample codes (SMP-{year}-{seq:06d}).

One row per year; next_sequence_number in sample_sequence_repository uses
SELECT ... FOR UPDATE to guarantee uniqueness under concurrent requests,
the same way complaint_sequence_repository works for complaint numbers.
"""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SampleSequence(Base):
    __tablename__ = "sample_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
