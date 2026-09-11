import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import SampleStatus


class Sample(Base):
    __tablename__ = 'samples'
    __table_args__ = (Index('ix_samples_inspection_id', 'inspection_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sample_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False, index=True
    )
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    seal_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collected_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('staff_profiles.id', ondelete='RESTRICT'), nullable=False
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SampleStatus] = mapped_column(
        SAEnum(SampleStatus, name='sample_status', values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=SampleStatus.COLLECTED,
    )
    dispatched_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('staff_profiles.id', ondelete='SET NULL'), nullable=True
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection: Mapped['Inspection'] = relationship()
    collected_by: Mapped['StaffProfile'] = relationship(foreign_keys=[collected_by_id])
    dispatched_to: Mapped['StaffProfile | None'] = relationship(foreign_keys=[dispatched_to_id])
    lab_test_result: Mapped['LabTestResult | None'] = relationship(back_populates='sample', uselist=False)