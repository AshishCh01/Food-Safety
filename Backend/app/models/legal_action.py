import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import LegalActionStatus, LegalActionType


class LegalAction(Base):
    __tablename__ = 'legal_actions'
    __table_args__ = (Index('ix_legal_actions_complaint_id', 'complaint_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False, index=True
    )
    lab_test_result_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('lab_test_results.id', ondelete='SET NULL'), nullable=True
    )
    initiated_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('staff_profiles.id', ondelete='RESTRICT'), nullable=False
    )
    fss_act_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action_type: Mapped[LegalActionType] = mapped_column(
        SAEnum(LegalActionType, name='legal_action_type', values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    fine_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    case_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    court_or_tribunal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[LegalActionStatus] = mapped_column(
        SAEnum(LegalActionStatus, name='legal_action_status', values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=LegalActionStatus.INITIATED,
    )
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    complaint: Mapped['Complaint'] = relationship(back_populates='legal_actions')
    lab_test_result: Mapped['LabTestResult | None'] = relationship()
    initiated_by: Mapped['StaffProfile'] = relationship()