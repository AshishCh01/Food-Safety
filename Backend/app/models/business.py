import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.core.geo_types import GeographyPoint, sync_location_from_lat_lon


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    # PostGIS geography point, kept in sync with latitude/longitude by the
    # event listener below. Powers proximity/spatial queries; the plain
    # latitude/longitude columns above remain the source of truth and are
    # what bounding-box map queries filter on directly.
    location: Mapped[str | None] = mapped_column(GeographyPoint, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    district: Mapped["District"] = relationship()


event.listen(Business, "before_insert", sync_location_from_lat_lon)
event.listen(Business, "before_update", sync_location_from_lat_lon)
