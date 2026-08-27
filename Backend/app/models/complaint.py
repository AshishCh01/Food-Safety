import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.core.geo_types import GeographyPoint, sync_location_from_lat_lon
from app.utils.enums import ComplaintPriority, ComplaintStatus


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_district_status", "district_id", "status"),
        Index("ix_complaints_district_priority", "district_id", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    complaint_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("complaint_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus, name="complaint_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=ComplaintStatus.SUBMITTED,
        index=True,
    )
    priority: Mapped[ComplaintPriority] = mapped_column(
        SAEnum(ComplaintPriority, name="complaint_priority", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=ComplaintPriority.MEDIUM,
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    # See Business.location - kept in sync with latitude/longitude by the
    # event listener below.
    location: Mapped[str | None] = mapped_column(GeographyPoint, nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    submitted_by: Mapped["User"] = relationship()
    business: Mapped["Business | None"] = relationship()
    district: Mapped["District"] = relationship()
    category: Mapped["ComplaintCategory"] = relationship()
    status_history: Mapped[list["ComplaintStatusHistory"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintStatusHistory.created_at"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan", order_by="Evidence.created_at"
    )


event.listen(Complaint, "before_insert", sync_location_from_lat_lon)
event.listen(Complaint, "before_update", sync_location_from_lat_lon)
