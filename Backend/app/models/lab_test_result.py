import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import LabVerdict


class LabTestResult(Base):
    __tablename__ = 'lab_test_results'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sample_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('samples.id', ondelete='CASCADE'), unique=True, nullable=False
    )
    food_analyst_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('staff_profiles.id', ondelete='RESTRICT'), nullable=False
    )
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    report_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verdict: Mapped[LabVerdict] = mapped_column(
        SAEnum(LabVerdict, name='lab_verdict', values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sample: Mapped['Sample'] = relationship(back_populates='lab_test_result')
    food_analyst: Mapped['StaffProfile'] = relationship()